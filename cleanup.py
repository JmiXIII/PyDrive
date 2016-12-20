# -*- coding: utf-8 -*-
"""
Created on Tue Dec 20 14:51:32 2016

@author: user11
"""

# This script removes the file revision created by the Zepto Ransomware and
# renames the file back to what it was before infection.
# This file CHANGES the drive. USE IT AT YOUR OWN RISK. I'M NOT RESPONSIBLE FOR ANY LOSE.
#
# Requirements :
#  * Avoid encoding problem by setting the python encoding before running the script
#   $ export PYTHONIOENCODING=utf8
#  * Turn on the Drive API and generate a OAuth client ID : https://developers.google.com/drive/v3/web/quickstart/python

from __future__ import print_function
import httplib2
import os
import json

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Drive API Python Quickstart'

def get_credentials():
    """
    Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
      os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'drive-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
      flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
      flow.user_agent = APPLICATION_NAME
      if flags:
        credentials = tools.run_flow(flow, store, flags)
      else:
        # Needed only for compatibility with Python 2.6
        credentials = tools.run(flow, store)
      print('Storing credentials to ' + credential_path)
    return credentials

def deleteFilesWithSuffix(suffix, service):
  results = service.files().list(
      corpus="domain",
      spaces="drive",
      pageSize=1000,
      orderBy="folder,modifiedTime desc,name",
      q="name contains '" + suffix + "'",
      fields="nextPageToken, files(id, name)"
        ).execute()
  items = results.get('files', [])
  if not items:
    print('No files found.')
  else:
    for item in items:
      if item['name'].endswith(suffix):
        try:
          deleteFile = service.files().delete(fileId=item['id']).execute()
          print("Deleted file : " + item['name'])
        except Exception as e:
          print("Could not delete file : " + item['name'] + ". Details : " + str(e))

def renameFile(fileId, originalFilename, service):
  try:
    print("Renaming file " + fileId + " to " + originalFilename)
    service.files().update(fileId=fileId, body={'name': originalFilename}, fields='name').execute()
  except Exception as e:
    print("Could not rename file " + fileId + " / Details : " + str(e))

def revertFiles(suffix, service):
  results = service.files().list(
      corpus="domain",
      spaces="drive",
      pageSize=1000,
      orderBy="folder,modifiedTime desc,name",
      #q="modifiedTime > '2016-09-04T12:00:00'",
      q= "name contains '" + suffix + "'",
      fields="nextPageToken, files(id, name)"
      ).execute()
  items = results.get('files', [])
  if not items:
    print('No files found.')
  else:
      for item in items:
        details = service.files().get(fileId=item['id'], fields="lastModifyingUser,name").execute()
        if details['name'].endswith(suffix):
            print("About to handle file " + details['name'] + " having id " + item['id'])
            revs = service.revisions().list(fileId=item['id'], fields="kind,revisions").execute()
            allrev = revs['revisions']
            lastRev = allrev[-1]
            if not lastRev['originalFilename'].endswith(suffix):
              # there was a rename problem during previous run -> fix it
              originalFilename = lastRev['originalFilename']
              renameFile(item['id'], originalFilename, service)
            elif len(allrev) > 1:
                origRev = allrev[-2]
                if lastRev['originalFilename'].endswith(suffix):
                  try:
                    print("Removing last revision of file " + details['name'])
                    revDel = service.revisions().delete(fileId=item['id'], revisionId=lastRev['id']).execute()
                    originalFilename = origRev['originalFilename']
                    renameFile(item['id'], originalFilename, service)
                  except Exception as e:
                    print("Could not process file : " + details['name'] + " / Details : " + str(e))

def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    deleteFilesWithSuffix('_HELP_instructions.html', service)
    revertFiles('nwZTXk71', service)

if __name__ == '__main__':
    main()
