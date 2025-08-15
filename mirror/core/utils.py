#utils.py defines common method or utilities

from .models import Sample, Image, Task, TestCase
from datetime import datetime, timezone, timedelta
from django.core import serializers
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth, TruncDate


def get_chart_data(chart_type):
    """
    method to get chart data by chart type
    Availble chart type:
        - sample_statistics
        - image
        - task_result_sum
        - task_st_this_week
    """

    # time defined for filter
    now = datetime.now(timezone.utc)
    first_day_of_month = now.replace(day=1)
    start_of_week = now - timedelta(days=now.weekday())
    six_month_ago = now - timedelta(days=180)

    label = []

    if chart_type == 'image':

        # label for the bar chart (past 6 month)
        past_6_month = []
        label_m = []
        for i in range(6):
            month_date = now - timedelta(days=(30 * i))
            label_m.append(month_date.strftime('%b'))
        past_6_month = label_m[::-1]
        label = past_6_month

        # category list
        cat_list = []
        for i in Image.CATEGORY_CHOICES:
            cat_list.append(i[0])

        # Images released count statistics in last 6 month
        img_cat_info = Image.objects.filter(release_date__gte=six_month_ago).annotate(
            month=TruncMonth('release_date')).values('month', 'category').annotate(count=Count('id')).order_by('month', 'category')
        for i in img_cat_info:
            i['month'] = i['month'].strftime('%b')

        dataset = {}
        for i in cat_list:
            dataset[i] = [0] * 6
        for info_by_month in img_cat_info:
            dataset[info_by_month['category']][past_6_month.index(info_by_month['month'])] = info_by_month['count']
     
    elif chart_type == 'task_result_sum':

        # label for the bar chart (past 6 month)
        past_6_month = []
        label_m = []
        for i in range(6):
            month_date = now - timedelta(days=(30 * i))
            label_m.append(month_date.strftime('%b'))
        past_6_month = label_m[::-1]
        label = past_6_month

        task_types = []
        for i in Task.TASK_CHOICES:
            task_types.append(i[0])

        task_sum = Task.objects.filter(time_trigger__gte=six_month_ago).annotate(
            month=TruncMonth('time_trigger')).values('month', 'task_category').annotate(
                result_pass=Count('id', filter=Q(result=True)), result_fail=Count('id', filter=Q(result=False))).order_by('month', 'task_category')
        for i in task_sum:
            i['month'] = i['month'].strftime('%b')

        dataset = {}
        for i in task_types:
            dataset[i] = {
                'pass': [0] * 6,
                'fail': [0] * 6,
            }
        for i in task_sum:
            dataset[i['task_category']]['pass'][past_6_month.index(i['month'])] += i['result_pass']
            dataset[i['task_category']]['fail'][past_6_month.index(i['month'])] += i['result_fail']

        # count task_cat 'full' in 'install' and 'test' and remove task_cat 'full' (install and test)
        for key in dataset['f']:
            dataset['i'][key] = [data_i + data_f for data_i, data_f in zip(dataset['i'][key], dataset['f'][key])]
            dataset['t'][key] = [data_i + data_f for data_i, data_f in zip(dataset['t'][key], dataset['f'][key])]

    elif chart_type == 'task_st_this_week':

        # label for the chart (weekday)
        day_of_week = []
        for i in range(7):
            day = now - timedelta(days=i)
            day_of_week.append(day.strftime('%a'))
        label = day_of_week[::-1]

        dataset = [0] * 7

        task_per_day = Task.objects.filter(time_trigger__gte=start_of_week).annotate(
            day=TruncDate('time_trigger')).values('day').annotate(count=Count('id')).order_by('day')
        for i in task_per_day:
            dataset[label.index(i['day'].strftime('%a'))] = i['count']


    elif chart_type == 'sample_statistics':
        dataset = {}
        spl_phase_count = Sample.objects.values('build_phase').annotate(count=Count('build_phase')).order_by('build_phase')
        for i in spl_phase_count:
            dataset[i['build_phase']] = i['count']

    else:
        return {'msg': 'charts type error'}

    context = {
        "label": label,
        'dataset': dataset,
    }

    return context


def get_task_data(tsk_id=None):
    """
    method to get task data
    """
    # if no task id provided, keep default to query all 'pending' (code 11) task data
    if tsk_id is None:
        task_data = Task.objects.filter(status='11').order_by('pk')
        res = []
        for i in task_data:
            tc_qs = i.testcases.values_list('id', flat=True)
            tc_list = list(tc_qs) 

            res.append({
                'task_id': i.pk,
                'task_cate': i.task_category,
                'task_status_code': i.status,
                'task_status': i.status_desc,
                'image_id': i.image.pk if i.image else None,
                'image_name': i.image.image_name if i.image else None,
                'image_filepath': i.image.file_path if i.image else None,
                'sample_id': i.sample.pk,
                'sample_ip': i.sample.ip,
                'sample_status_code': i.sample.status,
                'sample_status': i.sample.status_desc,
                'tc_list': tc_list,
                'contact': i.trigger_by.user.email,
                })
    else:
        try:
            task = Task.objects.get(pk=tsk_id)
            tc_qs = task.testcases.values_list('id', flat=True)
            tc_list = list(tc_qs)

            res = {
                'task_id': task.pk,
                'task_cate': task.task_category,
                'task_status_code': task.status,
                'task_status': task.status_desc,
                'image_id': task.image.pk if task.image else None,
                'image_name': task.image.image_name if task.image else None,
                'image_filepath': task.image.file_path if task.image else None,
                'sample_id': task.sample.pk,
                'sample_ip': task.sample.ip,
                'sample_status_code': task.sample.status,
                'sample_status': task.sample.status_desc,
                'tc_list': tc_list,
                'contact': task.trigger_by.user.email,
                }
        except Exception as e:
            return None

    return res


def get_sample_data(sample_id=None, ssid=None, st=None):
    """
    Method to get sample data by sample id or service tag + bios id
    """
    if sample_id is not None:
        try:
            sample_data = Sample.objects.get(pk=sample_id)
            res = {
                'id': sample_data.pk,
                'ip': sample_data.ip,
                'st': sample_data.service_tag,
                'ssid': sample_data.ssid,
                'dpn': sample_data.dpn,
                'status_code': sample_data.status,
                'status': sample_data.status_desc,
            }
        except Exception as e:
            return None

    elif ssid is not None and st is not None:
        try:
            sample_data = Sample.objects.get(service_tag=st, ssid=ssid)
            res = {
                'id': sample_data.pk,
                'ip': sample_data.ip,
                'st': sample_data.service_tag,
                'ssid': sample_data.ssid,
                'dpn': sample_data.dpn,
                'status_code': sample_data.status,
                'status': sample_data.status_desc,
            }
        except Exception as e:
            return None

    else:
        sample_data = Sample.objects.all()
        res = []
        for i in sample_data:
            res.append({
                'id': i.pk,
                'ip': i.ip,
                'st': i.service_tag,
                'ssid': i.ssid,
                'dpn': i.dpn,
                'status_code': i.status,
                'status': i.status_desc,
                })
    return res


def get_testcase_data(tc_id=None):
    """
    Method to get the testcase data
    """
    if tc_id is not None:
        try:
            tc = TestCase.objects.get(pk=tc_id)
            owner_profile = tc.owner
            res = {
                'id': tc.pk,
                'case_name': tc.case_name,
                'desc': tc.description,
                'script': tc.script,
                'is_remote': tc.is_remote,
                'is_root_required': tc.is_root_required,
                'ver': tc.version,
                'owner': owner_profile.user.email if owner_profile else None,
            }
        except Exception as e:
            return None
    else:
        tc = TestCase.objects.all()
        res = []
        for i in tc:
            owner_profile = i.owner
            res.append({
                'id': i.pk,
                'case_name': i.case_name,
                'desc': i.description,
                'script': i.script,
                'is_remote': i.is_remote,
                'is_root_required': i.is_root_required,
                'ver': i.version,
                'owner': owner_profile.user.email if owner_profile else None,
                })
    return res


def update_sample_status(spl_id, stat):
    """
    Method to update the sample status
    """
    try:
        spl = Sample.objects.get(pk=spl_id)
        if stat not in ['00', '10', '11', '12', '13', '20']:
            return -1
        spl.status = stat
        spl.save()
        return 0
    except Exception as e:
        return -1


def update_task_status(tsk_id, stat):
    """
    Method to update the task status
    """
    try:
        tsk = Task.objects.get(pk=tsk_id)
        if stat not in ['00', '11', '12', '13']:
            return -1
        tsk.status = stat
        tsk.save()
        return 0
    except Exception as e:
        return -1
