@echo off
REM
REM This is a helper script to start things so users don't have to know 
REM all the gory details until they want to.
REM

REM We have to start the AGNodeService for the node management to start
start /MIN AGNodeService.py

REM We have to start the AGServiceManager to host services for node management
start /MIN AGServiceManager.py

REM Then we start the UI
VenueClient.py