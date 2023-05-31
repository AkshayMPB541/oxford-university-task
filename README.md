This repo consist of automation code to automate deletion of remote developer environments when they reach end of their life span as defined by the organisation policy. The code assumes these remote environments are hosted on google cloud platform. This paradigm can be practiced on any infrastructure provider which supports immutability. Its a good practice if we can have remote developer environments which are dynamic in nature and short lived. It greatly improves developer productivity and has positive impact on environmental promotion process of new features and services. It also helps us utlizing the developer budget in the most efficient mannner as they short lived. This setup is also very carbon friendly making our developement process more greener.

The other benefits include:-

1) we can test dependencies eaily if we are using distributed architectures like databases, other services, Kafka system

2) We can test multiple versions of different services together at once

3) We can run regression test pack on developer environments early stages of SDLC to adopt shift left coding practices


To Run the script use pip3 install -r requirements.txt
and run "python3 project_destroyer.py" and to run "python3 -m unittest unit-test.py"