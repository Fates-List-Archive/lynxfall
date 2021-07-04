## Lynxfall RabbitMQ Worker documentation

Lynxfall RabbitMQ workers are a easy and robust way of handling messages/background tasks/queues. 
It uses RabbitMQ for the actual queue system, Redis for returning data from the worker and some custom code to make everything work.

### Creating a worker

Creating a worker requires you to do three things:

1) A launcher file to run your worker
2) Actual tasks (called backends on Lynxfall) for your worker to run
3) Add tasks to it using add_rmq_task

The below sections will deal with creating these two things.

#### The Launcher File

For extra security, you will need to first make a random secret called the worker key. You can use any random string generator to do this. Note that if this key is ever cracked or leaked, attackers may be able to gain arbitary code execution on your worker, so keep the worker key safe.
