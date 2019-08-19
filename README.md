# Demo Python Gateway

This Gateway serves as both an example of interacting with Major Tom using the Gateway API and 
a demo Satellite which responds to commands, generates telemetry, and uplinks/downlinks files. 

If you have any issues setting up/running this demo, 
either [make an issue](https://github.com/kubos/example-python-gateway/issues/new) on this repository
or [come talk to us on Slack](https://slack.kubos.com) and we'll get you sorted out! 

## Local Setup 

Clone locally to use it with Major Tom.

Requires Python 3.7+ and package requirements are in `requirements.txt`. Install with the command:

```pip3 install -r requirements.txt```

## Major Tom Setup

In addition to setting up your Local Environment, you'll need to make a Gateway in Major Tom! 
Once you've received your login credentials for Major Tom, make a new mission, 
and you'll be prompted to add a Gateway to that mission. 

Once you add the Gateway, make a note of the Gateway's __Authentication Token__ listed on the Gateway Page. 
You'll need it to run this demo Gateway. 

## Connect the Gateway

The `-h` (help) argument explains how to run the demo locally after you've set up the environment.
Access this by running the following command from the repository's top level directory: 

```python3 run.py -h```

If you are using this on a __Trial__ of Major Tom, you will most likely run this command: 

```python3 run.py -m app.majortom.cloud -g {YOUR-GATEWAY-AUTHENTICATION-TOKEN}```

For Example: 

```python3 run.py -m app.majortom.cloud -g 4b1273101901225a9d3df4882884b26e139cdeb49d2c1a50a51baf66c3a42623```

Once you run this, should should see Major Tom respond with a `hello` message:

```2019-08-19 12:04:46,151 - major_tom.major_tom - INFO - Major Tom says hello: {'type': 'hello', 'hello': {'mission': 'Demo'}}```

## What does this Demo Satellite do? 

Now that you've connected the gateway, it will automatically create a new satellite named "Space Oddity" and load in command definitions for it. 

You can now issue those commands to the satellite through the connected Gateway, which accomplish a wide variety of simulated tasks, all of which are explained by the description under each command. 

To find these commands, go to Major Tom under the mission you originally created and hover over the satellites icon on the sidebar. 
Space Oddity should be in the slider menu, and clicking on it will take you to its commanding page. 

Fire away! 

## What's Next? 

### Set up your Mission Dashboard

The Mission Dashboard allows you to monitor and control everything on the Mission. 
Add cards and play with their settings to see what you can do! 

### Integrate Your System

Now that you understand how the integration works, try augmenting the Demo Satellite to actually communicate with your hardware/software! 
Then you can begin controlling and monitoring your own spacecraft. 
