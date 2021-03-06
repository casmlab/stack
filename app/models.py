import json
import dateutil.parser
from datetime import datetime
from bson.objectid import ObjectId
from pymongo import MongoClient
from werkzeug import check_password_hash
from app import app
import traceback
import datetime

class DB(object):
    """
    A STACK wrapper to handle recurring interactions with MongoDB
    """
    def __init__(self):
        # Class instance connection to Mongo
        self.connection = MongoClient()

        # App-wide config file for project info access
        self.config_db = self.connection.config
        self.stack_config = self.config_db.config

    def create(self, project_name, password, hashed_password, description=None,
               admin=False, email=None):
        """
        Creates a project account with given name, password, and description
        """
        # Creates base STACK info (if doesn't exist)
        resp = self.stack_config.find_one({'module': 'info'})
        if resp is not None:
            doc = {'module': 'info', 'app': 'STACK', 'version': app.config['VERSION']}
            self.stack_config.insert(doc)

        status = 0
        message = None

        # Checks to see if project already exists
        resp = self.stack_config.find_one({'project_name': project_name})
        if resp:
            status = 0
            message = 'The project name %s is already taken. Please try again!' % project_name

        # If not, creates project
        else:
            # Creates an admin project login if creating an admin account
            if admin:
                project_doc = {
                    'project_name': project_name,
                    'password': hashed_password,
                    'description': description,
                    'configdb': None,
                    'collectors': None,
                    'admin': 1
                }
            # Creates a regular project account otherwise
            else:
                configdb = project_name + 'Config'

                project_doc = {
                    'project_name': project_name,
                    'password': hashed_password,
                    'description': description,
                    'email': email,
                    'collectors': [],
                    'configdb': configdb,
                    'admin': 0
                }

            # Try to insert project account doc; returns a failure if Mongo insert doesn't work
            try:
                self.stack_config.insert(project_doc)

                if admin:
                    status = 1
                    message = 'Admin account created successfully!'

            except:
                status = 0
                message = 'Project creation failed!'
                resp = self._generate_response(status, message)
                return resp

            # Creates account info for network modules if not an admin account
            if admin is False:
                resp = self.auth(project_name, password)
                if not resp['status']:
                    status = 0
                    message = 'Could not load new project info. Setup failed.'

                    resp = {'status': status, 'message': message}
                    return resp
                else:
                    # Creates a doc for each network
                    networks = app.config['NETWORKS']
                    for network in networks:
                        project_config_db = self.connection[configdb]
                        coll = project_config_db.config

                        doc = {
                            'module'            : network,
                            'processor'         : {'run': 0, 'restart': 0},
                            'inserter'          : {'run': 0, 'restart': 0},
                            'processor_active'  : 0,
                            'inserter_active'   : 0
                        }

                        try:
                            coll.insert(doc)
                            status = 1
                            message = 'Project account successfully created!'
                        except Exception as e:
                            status = 0
                            message = 'Network module setup failed for project! Try again.'

        resp = self._generate_response(status, message)
        return resp

    def auth(self, project_name, password):
        """
        Project auth function
        """
        auth = self.stack_config.find_one({'project_name': project_name})

        if auth and check_password_hash(auth['password'], password):
            status = 1
            project_id = str(auth['_id'])
            admin = auth['admin']
            message = 'Success'
        else:
            status = 0
            project_id = None
            admin = None
            message = 'Failed'

        resp = {'status': status, 'message': message, 'project_id': project_id, 'admin': admin}

        return resp

    def get_project_list(self):
        """
        Generic function that return list of all projects in stack config DB
        """
        projects = self.stack_config.find()

        if projects:
            status = 1
            project_count = self.stack_config.count()
            project_list = []

            for project in projects:
                project['_id'] = str(project['_id'])
                project['num_collectors'] = 0
                project['active_collectors'] = 0

                if project['collectors']:
                    project['num_collectors'] = len(project['collectors'])

                    active_colls = [c for c in project['collectors'] if c['active'] == 1]
                    project['active_collectors'] = len(active_colls)

                project_list.append(project)

            resp = {'status': status, 'message': 'Success', 'project_count': project_count, 'project_list': project_list}
        else:
            status = 0
            resp = {'status': status, 'message': 'Failed'}

        return resp

    def get_collector_ids(self, project_id):
        """
        When passed a project_id, will return a simple list of collectors and
        their corresponding IDs.
        """
        resp = self.get_project_detail(project_id)

        if not resp['status']:
            resp = {'status': 0, 'message': 'Project does not exist, please try again.'}
            return resp
        else:
            collectors = []
            project_name = resp['project_name']

            if resp['collectors']:
                for collector in resp['collectors']:
                    coll_info = {
                        'collector_name': collector['collector_name'],
                        'collector_id': collector['_id']
                    }
                    collectors.append(coll_info)

            resp = {
                'status': 1,
                'project_name': project_name,
                'collectors': collectors
            }
            return resp

    def get_project_detail(self, project_id):
        """
        When passed a project_id, returns that project's account info along
        with it's list of collectors
        """
        project = self.stack_config.find_one({'_id': ObjectId(project_id)})

        if not project:
            resp = {'status': 0, 'message': 'Failed'}
            return resp
        else:
            configdb = project['configdb']

            resp = {
                'status'                : 1,
                'message'               : 'Success',
                'project_id'            : str(project['_id']),
                'project_name'          : project['project_name'],
                'project_description'   : project['description'],
                'project_config_db'     : configdb,
                'admin'                 : project['admin']
            }

            if project['collectors'] is None:
                resp['collectors'] = None
            else:
                project_config_db = self.connection[configdb]
                coll = project_config_db.config

                collectors = []
                for item in project['collectors']:
                    collector_id = item['collector_id']

                    collector = coll.find_one({'_id': ObjectId(collector_id)})
                    collector['_id'] = str(collector['_id'])

                    collectors.append(collector)

                resp['collectors'] = collectors

            return resp

    def get_collector_detail(self, project_id,collector_id,project_name=None):
        """
        When passed a collector_id, returns that collectors details
        """
        project = self.get_project_detail(project_id)
	details=0
        if project['status']:
            configdb = project['project_config_db']

            project_config_db = self.connection[configdb]
            coll = project_config_db.config

            collector = coll.find_one({'_id': ObjectId(collector_id)})
            if collector:
                collector['_id'] = str(collector['_id'])
                resp = {'status': 1, 'message': 'Success', 'collector': collector}
            else:
                resp = {'status': 0, 'message': 'Failed'}
        else:
            resp = {'status': 0, 'message': 'Failed'}

        return resp

    def get_network_detail(self, project_id, network):
        """
        Returns details for a network module. To be used by the Controller.
        """
        project = self.get_project_detail(project_id)

        if project['status']:
            configdb = project['project_config_db']

            project_config_db = self.connection[configdb]
            coll = project_config_db.config

            network = coll.find_one({'module': network})
            if network:
                network['_id'] = str(network['_id'])
                resp = {'status': 1, 'message': 'Success', 'network': network}
            else:
                resp = {'status': 0, 'message': 'Failed'}
        else:
            resp = {'status': 0, 'message': 'Failed'}

        return resp

    def get_project_data_size(self,project_name):
	configdb=self.connection['config']	
	coll=configdb.config
	coll.create_index('project_name',unique=False)
	projectid_resp=coll.find({'project_name':str(project_name)},{'_id':1})
	projectid=projectid_resp[0]['_id']
	dbname=project_name+"_"+str(projectid)
	project_db=self.connection[dbname]
	
	return str(project_db.tweets.count())
    def get_term_details(self,project_name,network,collector_name,collector_id,term_id,project_id):
	try:		
		project = self.get_project_detail(project_id)
	
		if project['status']:
	            configdb = project_name+'_'+project_id
	            project_db = self.connection[configdb]
		    coll = project_db.tweets
		    resp=project_db.tweets.create_index('user.id_str',unique=False)
		    project_db.tweets.create_index('in_reply_to_user_id',unique=False)	
		    project_db.tweets.create_index('created_ts',unique=False)	
		    project_db.tweets.create_index('timestamp_ms',unique=False)
		    project_db.tweets.create_index('entities.user_mentions.id_str',unique=False)	
		    tweets = coll.find_one({'user.id_str':term_id})
		    dictvalue=self.Get_Set_OtherParameters(term_id,project_id,project_name,coll)	
		#    urlcounter=dictvalue['urlcounter']	
		    if tweets:
	                resp = {'status': 1, 'message': 'success', 
				'names':tweets['user']['screen_name'],
				'description':tweets['user']['description'], 
				'friends_count':str(tweets['user']['friends_count']),
				'location':tweets['user']['location'],
				'favouritecount':str(tweets['user']['favourites_count']),
				'followers':str(tweets['user']['followers_count']),
				'headercolor':tweets['user']['profile_text_color'],
				'statuscount':str(tweets['user']['statuses_count']),
				'totalurls':dictvalue['urlcounter'],
				'hashtagscounter':dictvalue['hashtagscounter'],
				'tweets_with_exclaim':dictvalue['exclamationmark'],
				'tweets_user_mentions':dictvalue['user_mentionscounts'],
				'total_retweets':dictvalue['retweetedcounts'],
				'total_tweets':dictvalue['totalcounts']	}
	            else:
	                resp = {'status': 0, 'message': 'Failed','reason':'No Data for the Term'}
		else:
			resp = {'status': 0, 'message': 'Failed','reason':'No Data for the Term'}
		return resp	
	except Exception as e:
		return {'message':'Failed','reason':str(e)}
#gets additional parameters like total url ,total exclamation in tweets,it will store data in the config db with the parameters
    def Get_Set_OtherParameters(self,term_id,project_id,projectname,collobject):
		try:
			dbname=projectname+'Config'
			flag=0
			########create database with time stamp
			project_db=self.connection['created_timestamp']
			timestampvalue=project_db.timestamp.find_one({'status':1},{'timestamp':1})
			
			#timestamp=timestamp_collect['timestamp']
			if(timestampvalue==None):
				#timestamp=timestampv
				timestamp=datetime.datetime.now()
				project_db.timestamp.insert({'timestamp':timestamp,'status':1})				
			else:
				timestamp=timestampvalue['timestamp']
				
			parameters=dict()
			valueid=term_id+project_id
			project_db=self.connection[dbname]
			collectionname='extraparameters_value'
			#tweetcount_in_db=0#collobject.find({'in_reply_to_user_id':long(term_id)}).count()
			tweetcount_in_db=collobject.find({'user.id_str':term_id}).count()
			tweetcount_config=project_db.extraparameters_value.find_one({'valueid':valueid},{'total':1,'hashtags':1,
	'urls':1,
	'user_mentions':1,
	'totalretweets':1,
	'favorite_count':1,
	'exclamationmark':1,
	'duplicatevalues':1,'statusinfo':1})
			if(tweetcount_config != None):
				flag=1
				statusinfo=0	
				if(((tweetcount_config['total'])!=tweetcount_in_db) or (str(tweetcount_config['statusinfo'])!=str(timestamp))):
						flag=0
						statusinfo=2
						project_db.extraparameters_value.remove({'valueid':valueid})	
				else:
						flag=1
						parameters['urlcounter']=tweetcount_config['urls']	
						parameters['hashtagscounter']=tweetcount_config['hashtags']
						parameters['exclamationmark']=tweetcount_config['exclamationmark']
						parameters['user_mentionscounts']=tweetcount_config['user_mentions']
						parameters['totalcounts']=tweetcount_config['total']
						parameters['retweetedcounts']=tweetcount_config['totalretweets']
						parameters['favorite_count']=tweetcount_config['favorite_count']
			
			if(flag==0):
				parameters['urlcounter']=0	
				parameters['hashtagscounter']=0	
				parameters['exclamationmark']=0
				parameters['user_mentionscounts']=0	
				parameters['totalcounts']=0	
				parameters['retweetedcounts']=0 
				parameters['favorite_count']=0	
				parameters['duplicates']=0	
				urlcounters=collobject.find({'user.id_str':term_id},{'in_reply_to_user_id':1,'text':1,'favorite_count':1,'counts.urls':1,'counts.hashtags':1,'counts.user_mentions':1,'retweeted':1})			
				for val in urlcounters:
					duplicatevalues=0
		
					if(duplicatevalues==0):
								if("!" in val['text']):
									parameters['exclamationmark']=parameters['exclamationmark']+1
								if(val['favorite_count']>=1):
									parameters['favorite_count']=parameters['favorite_count']+1
								if(val['retweeted']=='True'):
									parameters['retweetedcounts']=parameters['retweetedcounts']+1
								if(val['counts']['user_mentions']>=1):	
									parameters['user_mentionscounts']=parameters['user_mentionscounts']+1	
								if(val['counts']['urls']>=1):
									parameters['urlcounter']=parameters['urlcounter']+1
								if(val['counts']['hashtags']>=1):
									parameters['hashtagscounter']=parameters['hashtagscounter']+1


				parameters['totalcounts']=tweetcount_in_db
				result=project_db.extraparameters_value.insert({
	"valueid":term_id+project_id,
	"hashtags":parameters['hashtagscounter'],
	"urls":parameters['urlcounter'],
	"total":parameters['totalcounts'],
	"user_mentions":parameters['user_mentionscounts'],
	"totalretweets":parameters['retweetedcounts'],
	"favorite_count":parameters['favorite_count'],
	"exclamationmark":parameters['exclamationmark'],
	"statusinfo":timestamp,
	"duplicatevalues":parameters['duplicates']
	})
			return parameters
		except Exception as e:
			return str(e)
    	
    def get_term_accounttweets_details(self,project_name,network,collector_name,collector_id,term_id,project_id,createdts,tabstatus=1):
	try:		
		project = self.get_project_detail(project_id)
		tweettext=""
		tweetfromaccount=""
		created_date=""
		users=""
		i=0
		dict_key=0
		usertweet_data=dict()
		returntweetval=dict()
		usertweet_name=dict()		
		created_ts=dict()		
		updatecreatedts=createdts
		if project['status']:
	            configdb = project_name+'_'+project_id
	            project_db = self.connection[configdb]
		    coll = project_db.tweets
		    if(tabstatus==1):	
			    #returntweetval[tabstatus+"name"]=0
			    #returntweetval[tabstatus+"data"]=0
			    cursor=coll.find({'$or':[{'in_reply_to_user_id':long(term_id)},{'entities.user_mentions.id_str':term_id}]},{'text':1,'user.name':1,'created_ts':1,'_id':0}).sort([('timestamp_ms',-1)]).limit(200)					
			    for tweets in cursor:
					i=i+1
					#tweetsvalues[i]=tweets['text']
					updatecreatedts=tweets['created_ts']
					tweettext=tweettext+ "||" +tweets['text']	
					users=users+"||"+tweets['user']['name']
					created_date=created_date+"||"+str(tweets['created_ts'])
					if(i==20):
						
						dict_key=dict_key+1
						usertweet_data[dict_key]= tweettext
						usertweet_name[dict_key]=users
						created_ts[dict_key]=created_date
						created_date=""
						tweettext="" 
						users=""			 					
						i=0
		   	    if(dict_key<10):
				dict_key=dict_key+1
				usertweet_data[dict_key]= tweettext
				usertweet_name[dict_key]=users
				created_ts[dict_key]=created_date
			
						
		    if(tabstatus==2):
			    cursor=coll.find({'$and':[{'in_reply_to_user_id':None},{'user.id_str':term_id}]},{'text':1,'user.name':1,'created_ts':1,'_id':0}).sort([('timestamp_ms',-1)]).limit(200)	
			    for tweets in cursor:
					i=i+1
					updatecreatedts=tweets['created_ts']
					tweettext=tweettext+"||"+tweets['text']
					created_date=created_date+"||"+str(tweets['created_ts'])
					if(i==20):						
						dict_key=dict_key+1
						usertweet_data[dict_key]= tweettext
						usertweet_name[dict_key]=tweets['user']['name']
						created_ts[dict_key]=created_date
						tweettext="" 				
						i=0
			    if(dict_key<10):
				dict_key=dict_key+1
				usertweet_data[dict_key]= tweettext
				usertweet_name[dict_key]=users
				created_ts[dict_key]=created_date	
		    if i>-1:
			#t1=data['list']
			#key=str(tabstatus)+""
			returntweetval[str(tabstatus)+"tweets"]=usertweet_data
			returntweetval[str(tabstatus)+"users"]=usertweet_name
			returntweetval[str(tabstatus)+"created_ts"]=created_ts
	                resp = {'status': tabstatus, 'message': 'success', 'tweets':tweettext,'users':users,'createdts':str(updatecreatedts),'val':returntweetval,'limit':dict_key}
	            else:
	                resp = {'status': 0, 'message': 'Failed','reason':'No Data for the Term'}
		else:
			resp = {'status': 0, 'message': 'Failed','reason':'No Data for the Term'}
		return resp
	except Exception as e:
		return {'message':'Failed','reason':str(e)}

    def set_active_collectors(self,command,collector_id,db_name):
	project_db = self.connection[db_name]
	coll = project_db.config
	active=1
	if(command=='stop'):
		active=0
	coll.update({'collectors.collector_id':collector_id},{'$set':{'collectors.0.active':active}})
		
    def set_collector_detail(self, project_id, collector_name, network, collection_type, api_credentials_dict,
                             terms_list, api=None, languages=None, location=None, start_date=None, end_date=None):
        """
        Sets up config collection for a project collector
        """
        resp = self.stack_config.find_one({'_id': ObjectId(project_id)})
        project_name = resp['project_name']
        configdb = resp['configdb']

        if terms_list:
            terms = []
            for term in terms_list:
                # Sets term type based on network and api filter
                term_type = 'term'
                if network == 'twitter' and api == 'follow':
                    term_type = 'handle'
                elif network == 'twitter' and api == 'track':
                    term_type = 'term'
                elif network == 'facebook':
                    term_type = 'page'

                # Sets first history tracker
                history = {
                    'start_date': datetime.date(datetime.now()).isoformat(),
                    'end_date': 'current'
                }

                # Adds term to full list
                terms.append({'term': term, 'collect': 1, 'type': term_type, 'id': None, 'history': [history]})
        else:
            terms = None

        # Sets additional parameters - right now only used for Facebook
        params = {}
        if network == 'facebook':
            params['last'] = None
            # Set since param
            if start_date:
                params['since'] = start_date
            else:
                params['since'] = None
            # Set until param
            if end_date:
                params['until'] = end_date
            else:
                params['until'] = None


        # Creates full Mongo doc
        doc = {
            'project_id'        : project_id,
            'project_name'      : project_name,
            'collector_name'    : collector_name,
            'network'           : network,
            'collection_type'   : collection_type,
            'api'               : api,
            'api_auth'          : api_credentials_dict,
            'terms_list'        : terms,
            'params'            : params,
            'collector'         : {'run': 0, 'collect': 0, 'update': 0},
            'active'            : 0,
            'listener_running'  : False,
            'languages'         : languages,
            'location'          : location,
            'rate_limits'       : [],
            'error_codes'       : []
        }

        project_config_db = self.connection[configdb]
        coll = project_config_db.config
        dbnamevalue=project_name+"_"+str(project_id)
        # If collector already exists, warns the user
        resp = coll.find_one({'collector_name': collector_name})
        if resp is not None:
            status = 0
            message = 'Collector already exists. Please try again or update this collector!'
        else:
            try:
                coll.insert(doc)
                dbnamevalue=self.connection[dbnamevalue]
		#remove the 3 lines if things break,sets indexes in the project table of tweets collector
                dbnamevalue.tweets.create_index('id_str',unique=True)	
                dbnamevalue.tweets.create_index('user.id_str',unique=False)
		dbnamevalue.tweets.create_index('created_ts',unique=False)
		dbnamevalue.tweets.create_index('timestamp_ms',unique=False)
		dbnamevalue.tweets.create_index('entities.user_mentions.id_str',unique=False)	
				#####################################################################################
                resp = coll.find_one({'collector_name': collector_name})
                collector_id = str(resp['_id'])

                self.stack_config.update({'_id': ObjectId(project_id)}, {'$push': {'collectors': {
                    'name': collector_name, 'collector_id': collector_id, 'active': 0}}})
                status = 1
                message = 'Collector created successfully!'
            except Exception as e:
                print e
                status = 0
                message = 'Collector creation failed!'

        resp = self._generate_response(status, message)
        return resp

    def update_collector_detail(self, project_id, collector_id, **kwargs):
        """
        Updates provided fields for the identified collector; responds w/ a
        failure if fields aren't valid
        """
        resp = self.stack_config.find_one({'_id': ObjectId(project_id)})
        project_name = resp['project_name']
        configdb = resp['configdb']

        project_config_db = self.connection[configdb]
        coll = project_config_db.config

        collector = coll.find_one({'_id': ObjectId(collector_id)})

        # Final doc that will be used for updating
        update_doc = {}

        for key in kwargs.keys():
            # Everything but terms is a simple rewrite
            if key in collector.keys() and key != 'terms_list':
                update_doc[key] = kwargs[key]
            # Terms, need to update dates, etc.
            elif key == 'terms_list':
                collector = coll.find_one({'_id': ObjectId(collector_id)})
                terms = collector['terms_list']

                # If terms exist, update on a case by case
                if terms:
                    for term in kwargs['terms_list']:
                        # Try to find term in current list
                        try:
                            i = next(i for (i, d) in enumerate(terms) if d['term'] == term['term'])

                            # If the term itself has changed, update accordingly
                            if terms[i]['term'] != term['term']:
                                terms[i]['term'] = term['term']

                            # If collect status has changed, update accordingly
                            if terms[i]['collect'] != term['collect']:
                                # If we're stopping collecting, update the most recent collect date
                                if term['collect'] == 0 and 'history' in terms[i]:
                                    terms[i]['history'][-1]['end_date'] = datetime.date(datetime.now()).isoformat()
                                else:
                                    new_history_doc = {
                                        'start_date': datetime.date(datetime.now()).isoformat(),
                                        'end_date': 'current'
                                    }
                                    if 'history' not in terms[i]:
                                        terms[i]['history'] = []
                                    terms[i]['history'].append(new_history_doc)
                                # Finally, update the collect status
                                terms[i]['collect'] = term['collect']
                        # If it's not there, add first start / stop dates
                        except StopIteration:
                            term['history'] = [{
                                'start_date': datetime.date(datetime.now()).isoformat(),
                                'end_date': 'current'
                            }]
                            terms.append(term)

                    # Add the updated terms list to the update doc
                    update_doc['terms_list'] = terms

                # Otherwise, create new terms list array
                else:
                    for term in kwargs['terms_list']:
                        term['history'] = [{
                            'start_date': datetime.date(datetime.now()).isoformat(),
                            'end_date': 'current'
                        }]
                    update_doc['terms_list'] = kwargs['terms_list']

        # Finally, updated the collector
        try:
            coll.update({'_id': ObjectId(collector_id)}, {'$set': update_doc})

            status = 1
            message = 'Collector updated successfully.'
        except:
            status = 0
            message = 'Collector could not be updated, please try again.'

        resp = {'status': status, 'message': message}
        return resp

    def set_network_status(self, project_id, network, run=0, process=False, insert=False):
        """
        Start / Stop preprocessor & inserter for a series of network
        collections
        """
        # Finds project db w/ flags
        project_info = self.get_project_detail(project_id)
        configdb = project_info['project_config_db']

        # Makes collection connection
        project_config_db = self.connection[configdb]
        coll = project_config_db.config

        status = 0
        message = None

        if process:
            try:
                coll.update({'module': network},
                    {'$set': {'processor.run': run}})
                status = 1
                message = 'Success'
            except:
                message = 'Failed'
        if insert:
            try:
                coll.update({'module': network},
                    {'$set': {'inserter.run': run}})
                status = 1
                message = 'Success'
            except:
                message = 'Failed'

        resp = self._generate_response(status, message)
        return resp

    def set_collector_status(self, project_id, collector_id, collector_status=0, update_status=0):
        """
        Start / Stop an individual collector
        """

        # Finds project db w/ flags
        project_info = self.get_project_detail(project_id)
        configdb = project_info['project_config_db']

        # Makes collection connection
        project_config_db = self.connection[configdb]
        coll = project_config_db.config

        status = 0

        if collector_status:
            try:
                coll.update({'_id': ObjectId(collector_id)},
                    {'$set': {'collector': {'run': 1, 'collect': 1, 'update': 0}}})
                status = 1
                message = 'Success'
            except Exception as e:
                message = e
        elif update_status:
            try:
                coll.update({'_id': ObjectId(collector_id)},
                    {'$set': {'collector': {'run': 1, 'collect': 1, 'update': 1}}})
                status = 1
                message = 'Success'
            except Exception as e:
                message = e
        else:
            try:
                coll.update({'_id': ObjectId(collector_id)},
                    {'$set': {'collector': {'run': 0, 'collect': 0, 'update': 0}}})
                status = 1
                message = 'Success'
            except Exception as e:
                message = e

        resp = {'status': status, 'message': message}

        return resp

    def check_process_status(self, project_id, process, collector_id=None, module=None):
        """
        Checks Mongo to see if a referenced collector/processor/inserter is actively running

        :param project_id:
        :param process: 'collect' | 'process' | 'insert'
        :param collector_id: Only provided if referencing a collector
        :param module: For processor or inserters, which network module
        :return: {'status': 0|1, 'message': 'active'|'inactive'}
        """

        # Default status and message to be returned
        status = 0
        message = 'inactive'

        # Finds project db
        project_info = self.get_project_detail(project_id)
        configdb = project_info['project_config_db']

        # Makes collection connection
        project_config_db = self.connection[configdb]
        coll = project_config_db.config

        # Grabs active flag from Mongo collector module
        if process == 'collect':
            collector = coll.find_one({'_id': ObjectId(collector_id)})

            active = collector['active']
            if active:
                message = 'active'
        else:
            network_mod = coll.find_one({'module': module})

            # Grabs the active flag from Mongo network module
            if process == 'process':
                active = network_mod['processor_active']
            else:
                active = network_mod['inserter_active']

            if active:
                message = 'active'


        resp = {'status': status, 'message': message}
        return resp

    def get_storage_counts(self, project_id, network):
        """
        Grabs the count of stored documents in Mongo for the given project and network

        :param project_id:
        :param network:

        :return: count
        """
        # Loads the storage DB
        storagedb = self._load_project_storage_db(project_id)

        # Initiates storage count
        count = 0

        if network == 'twitter':
            count = storagedb.tweets.count()
        elif network == 'facebook':
            count = storagedb.facebook.count()

        return count

    def _load_project_config_db(self, project_id):
        """
        Utility method to load a project account's config DB

        :param project_id:

        :return: project_config_db connection
        """
        # Finds project db
        project_info = self.get_project_detail(project_id)
        configdb = project_info['project_config_db']

        # Makes a connection to the config db
        project_config_db = self.connection[configdb]

        return project_config_db

    def _load_project_storage_db(self, project_id):
        """
        Utility method to load a project account's storage DB

        :param project_id:

        :return: project_storage_db connection
        """
        # Finds project db
        project_info = self.get_project_detail(project_id)

        # Connects to the storage DB
        db_name = project_info['project_name'] + '_' + project_id
        project_storage_db = self.connection[db_name]

        return project_storage_db

    def _generate_response(self, status, message, content=None):
        """
        Utility message to generate a request response in a standardized format

        :param status - status code
        :param message - message to send w/ status code
        :param content - response content | None

        :return: resp = { 'status': 1|0, 'message':'message-text-here', 'content': ... }
        """
        return {
            'status': status,
            'message': message,
            'content': content
        }
