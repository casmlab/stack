import threading
import time

from bson.objectid import ObjectId
from facebook import Facebook, FacebookError

from app.processes import BaseCollector

e = threading.Event()


class CollectionListener(object):
    """
    Class to handle the connection to the Facebook API
    """
    def __init__(self, Collector):
        self.c = Collector
        self.fb = self.c.fb
        self.terms_list = self.c.terms_list

        self.post_count = 0
        self.rate_limit_count = 0
        self.error_count = 0

        # For logging
        self.thread = 'LISTENER:'

    def run(self):
        """
        Starts the Facebook collection - sends to proper method based on type
        """
        # TODO - initial sleep pattern = 10 minutes
        # TODO - POST implementation to listen
        # TODO - load in photos, need to actual store: collecting images off by default

        if self.c.collection_type == 'realtime':
            self.run_loop()
        elif self.c.collection_type == 'historical':
            self.run_search()

    def run_loop(self):
        """
        Infinite loop for real-time collections
        """
        run = True
        while run == True:

            # First, check to see if the thread has been set to shut down. If so, break
            thread_status = e.isSet()
            if thread_status:
                self.c.log('Collection thread set to shut down. Shutting down.', thread=self.thread)
                run = False
                break

            # TODO - since, until, paging logs, etc.



    def run_search(self):
        """
        One-time Graph API search for historical collections
        """

    def on_data(self, data):
        """
        Parses raw data and calls Collector's write() method to send to a file
        """
        # TODO - need to log last-item point each time since shut down could happen on any loop

    def on_disconnect(self):
        """
        Handles disconnect when thread is set to terminate
        """


class Collector(BaseCollector):
    """
    Extension of the STACK Collector for Facebook
    """
    def __init__(self, project_id, collector_id, process_name):
        BaseCollector.__init__(self, project_id, collector_id, process_name)
        self.thread_count = 0
        self.thread_name = ''
        self.l = None
        self.l_thread = None

        # First, authenticate with the Facebook Graph API w/ creds from Mongo
        self.fb = Facebook(client_id=self.auth['client_id'], client_secret=self.auth['client_secret'])

    def start_thread(self):
        """
        Starts the CollectionThread()
        """
        self.thread_count += 1
        self.thread_name = self.collector_name + '-thread%d' % self.thread_count

        self.log("Terms list length: %d" % len(self.terms_list))
        self.log("Querying the Facebook Graph API for term IDs...")

        success_terms = []
        failed_terms = []
        for item in self.terms_list:
            term = item['term']

            # If the term already has an ID, pass
            if item['id'] is not None:
                pass
            else:
                try:
                    term_id = self.fb.get_object_id(term)
                # Term failed - not valid
                except FacebookError as e:
                    self.log('Page %s does not exist or is not accessible.' % term, level='warn')
                    item['collect'] = 0
                    item['id'] = None
                    failed_terms.append(term)
                # On success
                else:
                    item['id'] = term_id
                    success_terms.append(term)

        self.log('Collected %d new IDs for Facebook collection.' % len(success_terms))
        self.log('IDs for the following %d terms could not be found:' % len(failed_terms))
        self.log(failed_terms)

        self.log('Updating in Mongo...')

        self.project_db.update({'_id': ObjectId(self.collector_id)},
            {'$set': {'terms_list': self.terms_list}})

        # Now set terms list to be the final list of IDs
        ids = [item['id'] for item in self.terms_list if item['id'] and item['collect']]
        self.terms_list = ids

        self.log('Now initializing Facebook listener...')

        # Sets up thread
        self.l = CollectionListener(self)
        self.l_thread = threading.Thread(name=self.thread_name, target=self.l.run)
        self.l_thread.start()

        self.collecting_data = True
        self.log('Started Facebook listener thread: %s' % self.thread_name)

    def stop_thread(self):
        """
        Stops the CollectionThread()
        """
        if self.update_flag:
            self.log('Received UPDATE signal. Attempting to restart collection thread.')
            self.db.set_collector_status(self.project_id, self.collector_id, update_status=1)
        if not self.collect_flag or not self.run_flag:
            self.log('Received STOP/EXIT signal. Attempting to stop collection thread.')
            self.db.set_colllector_status(self.project_id, self.collector_id, collector_status=0)
            self.collect_flag = 0

        e.set()
        wait_count = 0
        while self.l_thread.isAlive():
            wait_count += 1
            self.log('%d) Waiting on Facebook listener thread shutdown.' % wait_count)
            time.sleep(wait_count)

        self.collecting_data = False

        # TODO - Facebook count, limit, error logging