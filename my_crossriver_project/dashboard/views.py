from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse

from django.template import Context, loader

import boto3
import time
import json

from django.views.decorators.cache import cache_page

def index(request):
    template = loader.get_template("index.html")
    #return HttpResponse("Hello, world. You're at the polls index.")
    return HttpResponse(template.render())


def format_query_results(response):
    return None

@cache_page(None)
def get_amount_applied_for(request):
    
    try:
        yr = request.GET['year']
    except:
        return HttpResponse("ERROR: pass an year", status=500)
    query = f"""
select substr(issue_d, 5,4), sum(loan_amnt) as loan_applied, 
sum(funded_amnt) as loan_funded, sum(funded_amnt_inv) as loan_invested
from test_db.loan_info1 
where substr(issue_d, 5,4) = '{yr}'
group by substr(issue_d, 5,4)
    """
    ath = boto3.client('athena','us-east-1')
    r = ath.start_query_execution(QueryString=query, ResultConfiguration={'OutputLocation':'s3://aws-athena-query-results-197226845247-us-east-1/xyz/'})
    qid = r['QueryExecutionId']
    status = ath.get_query_execution(QueryExecutionId=qid)['QueryExecution']['Status']['State'] 
    cnt = 0
    while status not in ('SUCCEEDED','FAILED','CANCELLED'):
        if cnt > 10:
            break
        time.sleep(5)
        status = ath.get_query_execution(QueryExecutionId=qid)['QueryExecution']['Status']['State']
        cnt = cnt + 1
    if status != 'SUCCEEDED':
        data = json.dumps({'count':cnt, 'status':status})
    else:
        d = ath.get_query_results(QueryExecutionId=qid)
        data = { 
               'total_loan': d['ResultSet']['Rows'][1]['Data'][1]['VarCharValue'],
               'total_funded': d['ResultSet']['Rows'][1]['Data'][2]['VarCharValue'],
               'total_investor': d['ResultSet']['Rows'][1]['Data'][3]['VarCharValue']
               }
        #data = format_query_results(d)
        data = json.dumps(data)
    return HttpResponse(data)

@cache_page(None)
def get_grade(request):

    try:
        yr = request.GET['year']
    except:
        return HttpResponse("ERROR: pass an year", status=500)
    query = f"""select substr(issue_d, 1,3) as mnth, grade, sum(loan_amnt)/count(distinct id) as loan_applied, 
sum(funded_amnt) as loan_funded, sum(funded_amnt_inv) as loan_invested
from test_db.loan_info1 
where substr(issue_d, 5,4) = '{yr}'
group by substr(issue_d, 1,3), grade
order by  grade, mnth
    """
    ath = boto3.client('athena','us-east-1')
    r = ath.start_query_execution(QueryString=query, ResultConfiguration={'OutputLocation':'s3://aws-athena-query-results-197226845247-us-east-1/xyz/'})
    qid = r['QueryExecutionId']
    status = ath.get_query_execution(QueryExecutionId=qid)['QueryExecution']['Status']['State']
    cnt = 0
    while status not in ('SUCCEEDED','FAILED','CANCELLED'):
        if cnt > 10:
            break
        time.sleep(5)
        status = ath.get_query_execution(QueryExecutionId=qid)['QueryExecution']['Status']['State']
        cnt = cnt + 1
    if status != 'SUCCEEDED':
        data = json.dumps({'count':cnt, 'status':status})
    else:
        d = ath.get_query_results(QueryExecutionId=qid)
        order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        mths = [ x['Data'][0]['VarCharValue'] for x in d['ResultSet']['Rows']][1:]
        grades = [ x['Data'][1]['VarCharValue'] for x in d['ResultSet']['Rows']][1:]
        value = [ x['Data'][2]['VarCharValue'] for x in d['ResultSet']['Rows']][1:]
        data = []
        data_sorted = sorted(sorted( [zip(grades, mths, value)][0], key=lambda x: order.index(x[1])), key=lambda x: x[0])
        series = {}
        prev_grade = None
        for row in data_sorted:
             if prev_grade == row[0]:
                series['data'].append([row[1],row[2]])
             else:
                if prev_grade != None:
                    data.append(series)
                series = {'name':row[0],'data': [[row[1],row[2]]]}
                prev_grade = row[0]
        return HttpResponse(json.dumps(data))
    return HttpResponse(data)

@cache_page(None)
def get_volume(request):

    try:
        yr = request.GET['year']
    except:
        return HttpResponse("ERROR: pass an year", status=500)
    query = f"""select substr(issue_d, 1,3) as mnth, count(distinct id) as loan_volume
            from test_db.loan_info1
            where substr(issue_d, 5,4) = '{yr}'
            group by substr(issue_d, 1,3)
            order by mnth
           """
    ath = boto3.client('athena','us-east-1')
    r = ath.start_query_execution(QueryString=query, ResultConfiguration={'OutputLocation':'s3://aws-athena-query-results-197226845247-us-east-1/xyz/'})
    qid = r['QueryExecutionId']
    status = ath.get_query_execution(QueryExecutionId=qid)['QueryExecution']['Status']['State']
    cnt = 0
    while status not in ('SUCCEEDED','FAILED','CANCELLED'):
        if cnt > 10:
            break
        time.sleep(5)
        status = ath.get_query_execution(QueryExecutionId=qid)['QueryExecution']['Status']['State']
        cnt = cnt + 1
    if status != 'SUCCEEDED':
        data = json.dumps({'count':cnt, 'status':status})
    else:
        d = ath.get_query_results(QueryExecutionId=qid)
        order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        mths = [ x['Data'][0]['VarCharValue'] for x in d['ResultSet']['Rows']][1:]
        value = [ x['Data'][1]['VarCharValue'] for x in d['ResultSet']['Rows']][1:]
        data_dict = {x[0]:x[1] for x in zip(mths,value)}
        data = []
        for m in order:
            data.append([m, data_dict[m]])
        data = {'name':'Loan Volume','data':data}
        d = json.dumps(data)
        return HttpResponse(d)
