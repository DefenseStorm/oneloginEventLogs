#!/usr/bin/env python

import sys,os,getopt
import traceback
import os
import time
import datetime
import calendar
import pickle
import json

sys.path.insert(0, 'onelogin-python-sdk/src')
from onelogin.api.client import OneLoginClient

sys.path.insert(0, 'ds-integration')
from DefenseStorm import DefenseStorm

class integration(object):

    def writeOneLoginEvent(self, event):
        this_event = {}
        this_event['id'] = event.id
        this_event['created_at'] = "%d" %(event.created_at.replace(tzinfo=None) - datetime.datetime.utcfromtimestamp(0)).total_seconds()
        this_event['account_id'] = event.account_id
        this_event['user_id'] = event.user_id
        this_event['username'] = event.user_name
        this_event['event_type_id'] = event.event_type_id
        this_event['notes'] = event.notes
        this_event['ip_src'] = event.ipaddr
        this_event['actor_user_id'] = event.actor_user_id
        this_event['actor_user_name'] = event.actor_user_name
        this_event['assuming_acting_user_id'] = event.assuming_acting_user_id
        this_event['role_id'] = event.role_id
        this_event['role_name'] = event.role_name
        this_event['app_id'] = event.app_id
        this_event['onelogin_app_name'] = event.app_name
        this_event['group_id'] = event.group_id
        this_event['group_name'] = event.group_name
        this_event['otp_device_id'] = event.otp_device_id
        this_event['otp_device_name'] = event.otp_device_name
        this_event['policy_id'] = event.policy_id
        this_event['policy_name'] = event.policy_name
        this_event['actor_system'] = event.actor_system
        this_event['custom_message'] = event.custom_message
        this_event['operation_name'] = event.operation_name
        this_event['directory_sync_run_id'] = event.directory_sync_run_id
        this_event['directory_id'] = event.directory_id
        this_event['resolution'] = event.resolution
        this_event['client_id'] = event.client_id
        this_event['resource_type_id'] = event.resource_type_id
        this_event['error_description'] = event.error_description
        this_event['proxy_ip'] = event.proxy_ip
        this_event['risk_score'] = event.risk_score
        this_event['risk_reasons'] = event.risk_reasons
        this_event['risk_cookie_id'] = event.risk_cookie_id
        this_event['browser_fingerprint'] = event.browser_fingerprint

        this_event['timestamp'] = this_event['created_at']
        this_event['ol_timestamp'] = this_event['created_at']

        this_event['message'] = self.event_types[this_event['event_type_id']]['description']
        this_event['event_type'] = self.event_types[this_event['event_type_id']]['name']

        self.ds.writeJSONEvent(this_event)

        return


    def run(self):
        global time
        self.state_dir = self.ds.config_get('onelogin', 'state_dir')
        last_run = self.ds.get_state(self.state_dir)
        current_run = datetime.datetime.utcnow()

        if last_run == None:
            self.ds.log("INFO", "No datetime found, defaulting to last 12 hours for results")
            last_run = datetime.datetime.utcnow() - datetime.timedelta(hours=12)


        last_run_str = last_run.strftime("%Y-%m-%dT%H:%M:%SZ")
        current_run_str = current_run.strftime("%Y-%m-%dT%H:%M:%SZ")

        query_events_params = {
            'since': last_run_str,
            'until': current_run_str
        }


        self.ds.log('INFO', 'Retrieving logs from %s until %s' %(last_run_str,current_run_str))

        #self.onelogin = OneLoginClient(client_id=self.ds.config_get('onelogin', 'client_id'), client_secret = self.ds.config_get('onelogin', 'client_secret') ,region=self.ds.config_get('onelogin', 'region'))
        self.onelogin = OneLoginClient(client_id = self.ds.config_get('onelogin', 'client_id'), client_secret = self.ds.config_get('onelogin', 'client_secret'))

        self.onelogin.requests_timeout = 10

        event_types = self.onelogin.get_event_types()
        for event in event_types:
            self.event_types[event.id] = {}
            self.event_types[event.id]['name'] = event.name
            self.event_types[event.id]['description'] = event.description


        events = self.onelogin.get_events(query_events_params)

        for this_event in events:
            self.writeOneLoginEvent(this_event)

        self.ds.set_state(self.state_dir, current_run)

    
    def usage(self):
        print
        print os.path.basename(__file__)
        print
        print '  No Options: Run a normal cycle'
        print
        print '  -t    Testing mode.  Do all the work but do not send events to GRID via '
        print '        syslog Local7.  Instead write the events to file \'output.TIMESTAMP\''
        print '        in the current directory'
        print
        print '  -l    Log to stdout instead of syslog Local6'
        print
    
    def __init__(self, argv):

        self.testing = False
        self.send_syslog = True
        self.ds = None
        self.event_types = {}
    
        try:
            opts, args = getopt.getopt(argv,"htnld:",["datedir="])
        except getopt.GetoptError:
            self.usage()
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-h':
                self.usage()
                sys.exit()
            elif opt in ("-t"):
                self.testing = True
            elif opt in ("-l"):
                self.send_syslog = False
    
        try:
            self.ds = DefenseStorm('oneloginEventLogs', testing=self.testing, send_syslog = self.send_syslog)
        except Exception ,e:
            traceback.print_exc()
            try:
                self.ds.log('ERROR', 'ERROR: ' + str(e))
            except:
                pass


if __name__ == "__main__":
    i = integration(sys.argv[1:]) 
    i.run()
