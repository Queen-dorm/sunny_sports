#!/usr/bin/env python
#-*-coding:utf-8-*-

from uuid import uuid1

import datetime

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import (
        UserManager, BaseUserManager, AbstractBaseUser
        )
from django.db import transaction

from sp.models.status import * 
#from sp.models.role import CoachProperty
import role as role_model

# Create your models here.

class Role(models.Model):
    role = models.IntegerField(choices=ROLE_LIST, unique=True, primary_key=True)
    class Meta:
        app_label='sp'

    def __str__(self):
        return self.get_role_display()


class MyUserManager(BaseUserManager):

    @transaction.atomic
    def create_user(self, phone, nickname, email, role, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not phone:
            raise ValueError('Users must have an phone number')

        print phone

        if nickname and email:
            user = self.model(
                phone=phone,
                nickname=nickname,
                email=email,
            )
        elif nickname:
            user = self.model(
                phone=phone,
                nickname=nickname,
            )
        elif email:
            user = self.model(
                phone=phone,
                email=email,
            )
        else:
            user = self.model(
                phone=phone,
            )

        user.id = str(uuid1())
        user.set_password(password)
        user.last_login = timezone.now()
        user.save()
        r = Role.objects.get(role=int(role))
        ur = UserRole.objects.create(user=user, role=r) #用objects.create可以不用save()
        if r.get_role_display() == "coach":
            print "Create Coach"
            cp = role_model.CoachProperty(user=user)
            cp.save()
            role_model.Coach(property=cp).save()
        elif r.get_role_display() == "student":
            print "Create Student"
            import student.models as student
            sp = student.StudentProperty(user=user)
            sp.save()
            student.Student(property=sp).save()
        elif r.get_role_display() == "club":
            print "Create Club"
            from club.models import Club
            Club.objects.create(user=user)
        elif r.get_role_display() == "group":
            print "Create Group"
            from group.models import Group
            Group.objects.create(user=user)

        return user

    @transaction.atomic
    def create_superuser(self, phone, nickname, email, role, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(phone, nickname, email, role, password)
        user.is_admin = True
        user.is_staff = True
        user.save(using=self._db)
        return user

class MyUser(AbstractBaseUser):
    id = models.CharField(primary_key=True, max_length=40, db_index=True)
    role = models.ManyToManyField(Role, through='UserRole')
    nickname = models.CharField(max_length=255, unique=True, null=True, blank=True)
    email    = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    phone    = models.CharField(max_length=15, unique=True, db_index=True)
    #password = models.CharField(max_length=64) #password 在abstract class里有

    regist_time = models.DateTimeField(default=datetime.datetime.now,blank=True)
    is_active = models.BooleanField(default=True)
    is_staff  = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    REQUIRED_FIELDS = ['role','nickname','email'] #除了phone和password以外传给manager的
    USERNAME_FIELD = 'phone'

    objects = MyUserManager()

    class Meta:
        app_label='sp'

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

    def get_full_name(self):
        return "Fullname"

    def get_short_name(self):
        return "Shortname"

    def is_role(self, roles):
        for r in self.role.all():
            if r.get_role_display() in roles:
                return True
        return False

class UserRole(models.Model):
    user = models.ForeignKey(MyUser)
    role = models.ForeignKey(Role)
    is_first = models.BooleanField(default=True,choices=INFO_STATUS) #是否第一次登录
    class Meta:
        app_label='sp'


class Code(models.Model):
    phone = models.CharField(max_length=15)
    code = models.CharField(max_length=10)
    time = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        app_label='sp'

class PasswordDigitalSignature(models.Model):
    phone = models.CharField(max_length=15)
    signature = models.CharField(max_length=200)
    time = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        app_label='sp'

class Message(models.Model):
    title = models.CharField(max_length=1000) #消息标题
    sender = models.CharField(max_length=200, default="")
    cont = models.CharField(max_length=3000)  #消息内容
    time = models.DateTimeField(default=datetime.datetime.now) #发布时间

    class Meta:
        app_label='sp'

class UserMessage(models.Model):
    userrole = models.ForeignKey(UserRole)
    msg = models.ForeignKey(Message)
    checked = models.BooleanField(default=False) #是否查看过

    class Meta:
        app_label='sp'


