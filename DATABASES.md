# Database Structure

STACK uses MongoDB to store data, including configuration information. To explain the databases cretaed and their structure, we'll use an example from the [CASM Lab's](http://casmlab.org) "Rogue Feds" project. In this project, we are tracking "rogue" Twitter accounts that were created after President Trump gagged federal agencies in January 2017. We followed the instructions in [INSTALL.md](INSTALL.md), and the following databases were created.

| Database | Collection(s) | What's in there|
|---|---|---|
|rogueConfig|config| collector name, Twitter OAuth info, list of accounts to follow |
|rogue_588aa42321e3853f8ac3c954|tweets| data Twitter's API returns|
|rogue\_588aa42321e3853f8ac3c954\_delete|tweets| tweets with delete requests|

