from django.shortcuts import render, get_object_or_404
from profiles.models import User
from providers.models import Job
from providers.views import publish_to_topic_mqtt
from datetime import datetime, timedelta
from pytz import timezone
from scheduler.settings import TIME_ZONE
from random import randint 
from scheduler.settings import USE_FABRIC
import fabric.views as fabric
import json
import csv
import random
from controller.mincost import minimize_total_cost
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
# import zmq

# # Create your views here.
# zmq_context = zmq.Context()

file_path = "/home/user/Documents/Serverless_Scheduler/SchedInfo.csv"
file_path_2="/home/user/Documents/Serverless_Scheduler/joblist.csv"
job_queue = []
def handle_request_queue(request,service) :
    if service.active:
            # temp_time = datetime.now(tz=timezone(TIME_ZONE))
            # response, provider, providing_time, job_id = request_handler(request, service, temp_time)
            find_provider(service)
    else:
        messages.error(request, "This service is disabled")

    # print("Response", response)
    # return JsonResponse(
    #               {'result': response['Result'],
    #                'providing_time': providing_time,
    #                'pull_time': response['pull_time'],
    #                'run_time': response['run_time'],
    #                'total_time': response['total_time'],
    #                'provider': provider, 
    #                'job_id': job_id})

    # do the logic
    #then call request_handler on each job that is assigned.

    pass
def request_handler(data,service,start_time,run_async = False):
    print("In request handler.")
    provider = None
    while(provider == None):
        provider = find_provider(service)
    print(provider)
    
    job = Job.objects.create(provider = provider, start_time = start_time)
    job.save()

    if USE_FABRIC:
        r = fabric.invoke_new_job(str(job.id), str(service.id), str(service.developer_id),
                                        str(provider.id), provider_org="Org1")
        if 'jwt expired' in r.text or 'jwt malformed' in r.text or 'User was not found' in r.text:
            token = fabric.register_user()
            r = fabric.invoke_new_job(str(job.id), str(service.id), str(service.developer_id),
                                        str(provider.id), provider_org="Org1",token=token)

    task_link = service.docker_container 
    task_developer = service.developer
    input_val = data['input']
    response_decoded = None
    # if(data['chained'] == True): 
    #     for i in range(data['numberOfInvocations']):
    #         response = publish_to_topic(data['runMultipleInvocations'], data['numberOfInvocations'], data['chained'], input_val, provider,task_link,task_developer, job.id)
    #     # total_time = response['pull_time'] + response['run_time']
    #         response_decoded = json.loads(response.decode("utf-8"))
    #         input_val = int(response_decoded['Result'])
    # for i in range(data['numberOfInvocations']):
    #response = publish_to_topic(data['runMultipleInvocations'], data['numberOfInvocations'], data['chained'], input_val, provider,task_link,task_developer, job.id)
    #print("abt to pub to mqtt")
    response = publish_to_topic_mqtt(data['runMultipleInvocations'], data['numberOfInvocations'], data['chained'], input_val, provider,task_link,task_developer, job.id)

    response_decoded = json.loads(response.decode("utf-8"))
    # response_decoded = json.loads(response)
    print("response from provider: ", response_decoded)
    job.refresh_from_db()
    job.pull_time = response_decoded['pull_time']
    job.run_time = response_decoded['run_time']
    job.total_time = response_decoded['total_time']
    job.cost = (response_decoded['total_time'])
    job.response = response_decoded['Result']
    job.finished = True
    job.save()
    providing_time = int(((job.ack_time - job.start_time)/timedelta(microseconds=1))/1000) # Providing time in milliseconds
    if USE_FABRIC:
        r = fabric.invoke_received_result(str(job.id))
        if 'jwt expired' in r.text or 'jwt malformed' in r.text or 'User was not found' in r.text:
            token = fabric.register_user()
            r = fabric.invoke_received_result(str(job.id), token=token)
    return response_decoded, provider.id, providing_time, str(job.id)
    #handle response

def request_handler_1(data,service,start_time,run_async = False):
    # print("In request handler.")
    # provider = None
    # while(provider == None):
    #     provider = find_provider(service)
    # print(provider)
    
    job = Job.objects.create(provider = None, start_time = start_time)
    job.save()
    jobs_queue.append(job)
    if USE_FABRIC:
        r = fabric.invoke_new_job(str(job.id), str(service.id), str(service.developer_id),
                                        str(None), provider_org="Org1")
        if 'jwt expired' in r.text or 'jwt malformed' in r.text or 'User was not found' in r.text:
            token = fabric.register_user()
            r = fabric.invoke_new_job(str(job.id), str(service.id), str(service.developer_id),
                                        str(None), provider_org="Org1",token=token)

    task_link = service.docker_container 
    task_developer = service.developer
    input_val = data['input']
    response_decoded = None
    # if(data['chained'] == True): 
    #     for i in range(data['numberOfInvocations']):
    #         response = publish_to_topic(data['runMultipleInvocations'], data['numberOfInvocations'], data['chained'], input_val, provider,task_link,task_developer, job.id)
    #     # total_time = response['pull_time'] + response['run_time']
    #         response_decoded = json.loads(response.decode("utf-8"))
    #         input_val = int(response_decoded['Result'])
    # for i in range(data['numberOfInvocations']):
    #response = publish_to_topic(data['runMultipleInvocations'], data['numberOfInvocations'], data['chained'], input_val, provider,task_link,task_developer, job.id)
    #print("abt to pub to mqtt")
    response = publish_to_topic_mqtt(data['runMultipleInvocations'], data['numberOfInvocations'], data['chained'], input_val, provider,task_link,task_developer, job.id)

    response_decoded = json.loads(response.decode("utf-8"))
    # response_decoded = json.loads(response)
    print("response from provider: ", response_decoded)
    job.refresh_from_db()
    job.pull_time = response_decoded['pull_time']
    job.run_time = response_decoded['run_time']
    job.total_time = response_decoded['total_time']
    job.cost = (response_decoded['total_time'])
    job.response = response_decoded['Result']
    job.finished = True
    job.save()
    providing_time = int(((job.ack_time - job.start_time)/timedelta(microseconds=1))/1000) # Providing time in milliseconds
    if USE_FABRIC:
        r = fabric.invoke_received_result(str(job.id))
        if 'jwt expired' in r.text or 'jwt malformed' in r.text or 'User was not found' in r.text:
            token = fabric.register_user()
            r = fabric.invoke_received_result(str(job.id), token=token)
    return response_decoded, provider.id, providing_time, str(job.id)
    #handle response
        
def calculate_cost(total_time):
    return total_time*0.01

def find_provider(service):

    ready_providers = User.objects.filter(
        active = True , ready = True , 
        # last_ready_signal__gte = datetime.now(tz=timezone(TIME_ZONE)) - timedelta(minutes=10000)
    )

    print("Ready Providers: \n", ready_providers)
    
    if len(ready_providers) == 0: 
        return

    max_provider = None
    max_invocations = -1
    provider_choices= []

    for provider_to_search in ready_providers:
        with open(file_path, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                provider = row['Provider']
                function = int(row['Function'])
                invocations = int(row['Invocations'])

                # Check if the row matches the criteria
                if provider == str(provider_to_search.user_id) and function == (service.id - 7):
                    provider_choices.append({'invocations': invocations, 'provider': provider_to_search.id})
                    # max_provider = provider
                    # max_invocations = invocations

    # sort
    if (len(provider_choices)< 1) :
        max_provider = random.choice(ready_providers)

    elif (len(provider_choices)==1):
        max_provider = get_object_or_404(User, pk=provider_choices[0]['provider'])
    else:
        provider_choices.sort(key=lambda x: x['invocations'], reverse=True)
        max_provider = get_object_or_404(User, pk = random.choice(provider_choices[0:2])['provider'])

    print("Scheduler is chosing this provider -> ", max_provider)
    updated_data = []
    flag = False
    if(max_provider != None):
        # Read the CSV file and update the values
        with open(file_path, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                provider = row['Provider']
                function = int(row['Function'])
                invocations = int(row['Invocations'])

                # Check if the row matches the criteria for update
                if provider == str(max_provider.user_id) and function == (service.id - 7):
                    flag = True
                    row['Invocations'] = str(int(invocations)+1)

                updated_data.append(row)

    if(flag == False):
        updated_data.append({'Provider': max_provider.user_id, 'Function': (service.id - 7), 'Invocations': 1})

    print(updated_data)

    with open(file_path, mode='w', newline='') as csv_file:
        fieldnames = ['Provider', 'Function', 'Invocations']
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        # Write the header
        csv_writer.writeheader()

        # Write the updated rows
        csv_writer.writerows(updated_data)

    return max_provider



def train_regression_model(training_data):
    X = []
    y = []
    for data in training_data:
        X.append([data["cpu_usage"] * data["cpu_efficiency_score"], 
                  data["memory_usage"] * data["memory_efficiency_score"]])
        y.append(data["actual_runtime"])

    model = LinearRegression()
    model.fit(X, y)
    return model

def predict_runtime(service, provider, model):

    ref_service_list = load_data_from_file("TrainingData/Reference_Provider_Data.txt")
    for item in ref_service_list:
        if(item['service']==service):
            reference_cpu_usage=item['cpu_usage']
            reference_memory_usage=item['memory_usage']
            break
    global cpu_efficiency_score, memory_efficiency_score

    # For training in scheduler, instead of globals use provider.cpu_efficiency_score and provider.memory_efficiency_score
    X = np.array([[reference_cpu_usage * cpu_efficiency_score, reference_memory_usage * memory_efficiency_score]])
    return model.predict(X)


def trainAndPredict(run_vars):
    #run_vars has  cpu_usage, memory_usage, actual_runtime (of providers required for training not prediction) they will be loaded from file
    #It also has service (task link) (to get corresponding reference stats), eff_scores for training+prediction the ones which we use in this function
    #TRAINING
    training_data=load_data_from_file("TrainingData/eff_score_data.txt")
    model = train_regression_model(training_data)
    #PREDICTION
    dummy_provider = 0 # this provider would be real if this were to run in the scheduler. Here it is useless as we use globals.
    predicted_runtime = predict_runtime(run_vars['service'], dummy_provider, model)
    return predicted_runtime[0]


def train_regression_model(training_data):
    X = []
    y = []
    for data in training_data:
        X.append([data["cpu_usage"] * data["cpu_efficiency_score"], 
                  data["memory_usage"] * data["memory_efficiency_score"]])
        y.append(data["actual_runtime"])

    model = LinearRegression()
    model.fit(X, y)
    return model

def predict_runtime(service, provider, model):

    ref_service_list = load_data_from_file("TrainingData/Reference_Provider_Data.txt")
    for item in ref_service_list:
        if(item['service']==service):
            reference_cpu_usage=item['cpu_usage']
            reference_memory_usage=item['memory_usage']
            break
    global cpu_efficiency_score, memory_efficiency_score

    # For training in scheduler, instead of globals use provider.cpu_efficiency_score and provider.memory_efficiency_score
    X = np.array([[reference_cpu_usage * cpu_efficiency_score, reference_memory_usage * memory_efficiency_score]])
    return model.predict(X)


def trainAndPredict(run_vars):
    #run_vars has  cpu_usage, memory_usage, actual_runtime (of providers required for training not prediction) they will be loaded from file
    #It also has service (task link) (to get corresponding reference stats), eff_scores for training+prediction the ones which we use in this function
    #TRAINING
    training_data=load_data_from_file("TrainingData/eff_score_data.txt")
    model = train_regression_model(training_data)
    #PREDICTION
    dummy_provider = 0 # this provider would be real if this were to run in the scheduler. Here it is useless as we use globals.
    predicted_runtime = predict_runtime(run_vars['service'], dummy_provider, model)
    return predicted_runtime[0]

#have to add job_status get method 
def joblist(assignment):
    dict_prov = {}
    status='waiting'
    for j,p in assignment.items():
        waiting_time=j.queue_time
        dict_prov[p].append(waiting_time,j,status)
    

    with open(file_path_2,mode='w') as csv_file:
        writer=csv_writer=csv.DictWriter(csv_file,fieldnames=['Provider'])
        writer.writeheader()
        for p,val in dict_prov.items():
            writer.writerow({p:val})
    
def assign_jobs():
    with open(file_path_2,mode='r') as csv_file:
        csv_reader=csv.DictReader(csv_file)
        for provider , job in csv_reader:
            if job.status=='waiting':
                job.status='running'
                request_handler(job.data,job.service,job.start_time)            
        
def find_providers_mincost(service):
    job_queue.append(service)
    # TODOz
    ready_providers = User.objects.filter(
         active = True 
        # last_ready_signal__gte = datetime.now(tz=timezone(TIME_ZONE)) - timedelta(minutes=10000)
    )

    print("Ready Providers: \n", ready_providers)
    
    if len(ready_providers) == 0: 
        return

    max_provider = None
    max_invocations = -1
    provider_choices= [r.id for r in ready_providers]

    # for provider_to_search in ready_providers:
    #     with open(file_path, mode='r') as csv_file:
    #         csv_reader = csv.DictReader(csv_file)
    #         for row in csv_reader:
    #             provider = row['Provider']
    #             function = int(row['Function'])
    #             invocations = int(row['Invocations'])

    #             # Check if the row matches the criteria
    #             if provider == str(provider_to_search.user_id) and function == (service.id - 7):
    #                 provider_choices.append({'invocations': invocations, 'provider': provider_to_search.id})
    #                 # max_provider = provider
    #                 # max_invocations = invocations

    # sort
    # if (len(provider_choices)< 1) :
    #     max_provider = random.choice(ready_providers)
        
    cost_matrix= get_predicted_runtimes(job_queue)
    delay = {}
    if (len(provider_choices)==1):
        max_provider = get_object_or_404(User, pk=provider_choices[0])
    else:
        # TODO
        # Here select the right code.
        # provider_choices.sort(key=lambda x: x['invocations'], reverse=True)
        assignment , _ = minimize_total_cost(provider_choices, service, cost_matrix, delay)
        joblist(assignment)
        assign_jobs()
        provider_choices.sort(key=lambda x: x['invocations'], reverse=True)
        max_provider = get_object_or_404(User, pk = random.choice(provider_choices[0:2])['provider'])

def choice(max_provider,service):
    print("Scheduler is chosing this provider -> ", max_provider)
    updated_data = []
    flag = False
    if(max_provider != None):
        # Read the CSV file and update the values
        with open(file_path, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                provider = row['Provider']
                function = int(row['Function'])
                invocations = int(row['Invocations'])

                # Check if the row matches the criteria for update
                if provider == str(max_provider.user_id) and function == (service.id - 7):
                    flag = True
                    row['Invocations'] = str(int(invocations)+1)

                updated_data.append(row)

    if(flag == False):
        updated_data.append({'Provider': max_provider.user_id, 'Function': (service.id - 7), 'Invocations': 1})

    print(updated_data)

    with open(file_path, mode='w', newline='') as csv_file:
        fieldnames = ['Provider', 'Function', 'Invocations']
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        # Write the header
        csv_writer.writeheader()

        # Write the updated rows
        csv_writer.writerows(updated_data)

    return max_provider
def get_providers():
    providers_to_assign = User.objects.filter(
        active = True  
    )
    return providers_to_assign

def get_predicted_runtimes(services):
    a=0
    cost_matrix = {}
    return cost_matrix
    # returns providers list
    # return cost_matrix with multiple invocations as different columns
    