# -*- coding:utf-8 -*-
import json

from django.http import HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from django.template import Context, Template
from django.db.models import F
from django.core.context_processors import csrf
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from sunny_sports.sp.models import *
from sunny_sports.sp.models.association import *
from sunny_sports.sp.models.role import *
from sunny_sports.sp.models.models import *

from forms import *

@login_required()
def centre(req):
    return render_to_response('centre/base.html')

@login_required()
def test_check(req, train_id=None):
    
    if req.method == "GET":
        train_id = req.GET.get("t_id",None)
        print "test_check, id %s"%train_id
        if train_id and len(train_id) > 0: #有编号的话就返回对应课程的人名单
            c_t = CoachTrain.objects.filter(train_id=train_id, train__pub_status=0, train__sub_status=1) #已提交但未发表
            #train = Train.objects.get(id=train_id)
            #filter return a list
            #get return an item
            if len(c_t) > 0:
                train = c_t[0].train
                return render_to_response('centre/test_check2.html',{"c_t":c_t, "train":train})
            else:
                return HttpResponse("<h2>没有该课程的审核请求</h2>")
        else:#否则返回待审核列表
            c_t = CoachTrain.objects.filter(train__pub_status=0, train__sub_status=1) #这里查的是Train的status，是联合两个表的查询，用两个_
            print len(c_t)
            ctlist = [i.train for i in c_t]
            jtlist = []
            return render_to_response('centre/test_check.html',{"ctlist":ctlist, "jtlist":jtlist})

@login_required()
def check_pass(req):
    """
    审核批准后
    """
    if req.method == "POST":
        t_id = req.POST.get("t_id")
        if int(req.POST.get("pass", 0)): #审核通过
            Train.objects.filter(id=t_id).update(pub_status=1)
            Train.objects.filter(id=t_id).update(sub_status=1)
            # generate certificate
            ns = req.POST.get("cert",{}).keys() #get number list获得审核通过的学号列表 
            pass_c_t = CoachTrain.objects.filter(number__in=ns, train_id=t_id)            
            not_pass_c_t = CoachTrain.objects.filter(train_id=t_id).exclude(number__in=ns)
            pass_c_t.update(certificate=str(t_id)+str(F('number')))

            # 发布消息通知
            title = u"考试结果"
            content = u"恭喜培训%s考试通过"%t_id
        else: #审核不通过
            Train.objects.filter(id=t_id).update(sub_status=2)
            Train.objects.filter(id=t_id).update(pub_status=0)
        return JsonResponse({"success":True})
    else:
        return JsonResponse({"success":False})


@login_required()
def history_view(req):
    if req.method == "GET":
        train_id = req.GET.get("t_id",None)
        if train_id and len(train_id) > 0: #有编号的话就返回对应课程的人名单
            c_t = CoachTrain.objects.filter(train_id=train_id, train__pub_status=1)
            if len(c_t) > 0:
                train = c_t[0].train
                return render_to_response('centre/history_view2.html',{"c_t":c_t, "train":train, "base":"./centre/base.html"})
            else:
                return HttpResponse("<h2>没有该课程的历史信息</h2>")
        else:#否则返回课程列表
            c_t = CoachTrain.objects.filter(train__pub_status=1) #这里查的是Train的status，是联合两个表的查询，用两个_
            ctlist = [i.train for i in c_t]
            jtlist = []
            return render_to_response('centre/history_view.html',{"ctlist":ctlist, "jtlist":jtlist})

@login_required()
def history_print(req, train_id=None):
    """
    生成csv表格并下载
    """
    if train_id and len(train_id) > 0:
        return csv_generate()
    else:
        return "Wrong Train id"

@login_required()
def msg_publish(req):
    """
    """
    if req.method == 'POST': #如果是提交表单内容
        print req.POST
        post = req.POST.copy()
        if post.get("stu", False):
            post["stu"] = True
        if post.get("coach", False):
            post["coach"] = True
        if post.get("judge", False):
            post["judge"] = True
        print post
        form = MessagePublishForm(post)
        print form.is_valid()
        if form.is_valid():
            form.save()
            return HttpResponseRedirect("msg_publish")
    else: # GET 方法请求消息发送页面
        form = MessagePublishForm()
        return render_to_response('centre/msg_publish.html', {'form':form}, RequestContext(req))


@login_required()
def password_page(req):
    """
    """
    return render_to_response('centre/password.html', RequestContext(req))

@login_required()
def org_manage(req):
    if req.method == "GET":
        orgs = CoachOrg.objects.all()
        return render_to_response('centre/org_manage.html', {"orgs":orgs}, RequestContext(req))

@login_required()
@transaction.atomic
def org_info(req):
    if req.method == "GET":
        num = req.GET.get("org_num")
        co = None
        if num:
            co = CoachOrg.objects.filter(org_num=num)
        if num and len(co) > 0:
            return render_to_response('centre/org_info.html', {"coachorg":co[0]}, RequestContext(req))
        else:
            return render_to_response('centre/org_info.html', {}, RequestContext(req))
    else:
        data = req.POST.copy()
        num = data.get("orgnum")
        for k in ["orgnum",'phone','orgname']:
            if not data.has_key(k) or len(data[k].strip()) == 0:
                return JsonResponse({},status=400)
        co = CoachOrg.objects.filter(org_num=num) | CoachOrg.objects.filter(user__phone=data.get('phone'))
        #如果数据库里没有记录，证明是添加新组织
        if len(co) == 0:
            print "add coachorg"
            phone = data.get('phone')
            r_id = 1
            user = MyUser.objects.create_user(phone = phone, nickname=None, email=None, role=r_id, password = num)
            co = CoachOrg(user=user)
        else:
            co = co[0]

        co.org_num = num
        co.name = data["orgname"]
        co.user.phone = data["phone"]
        if data.has_key("director"):
            co.director = data["director"]
        if data.has_key("province"):
            co.province = data.get("province","")
        if data.has_key("city"):
            co.city = data.get("city","")
        if data.has_key("dist"):
            co.dist = data.get("dist","")
        if data.has_key("address"):
            co.address = data.get("address","")
        try:
            co.save()
        except:
            return JsonResponse({'success':False})
        return JsonResponse({'success':True})

@login_required()
def add_member(req):
    if req.method == "GET":
        phone = req.GET.get("phone")
        print phone
        c = Coach.objects.filter(property__user__phone=phone)
        if len(c) > 0:
            return JsonResponse({"name":c[0].property.name })
        else:
            return JsonResponse({"name":None})

    else:
        phone = req.POST.get("phone")
        name = req.POST.get("name")
        t_id = req.POST.get("t_id")
        print t_id
        c = Coach.objects.filter(property__user__phone=phone, property__name=name)
        if len(c) > 0:
            c = c[0]
            ct = CoachTrain.objects.create(coach=c, train=Train.objects.get(id=t_id), status=2)
            ct.train.cur_num = ct.train.cur_num + 1
            ct.save()
            return JsonResponse({'success':True})
        else:
            return JsonResponse({'success':False})



