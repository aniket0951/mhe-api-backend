from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from django.core.validators import MaxValueValidator
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from apps.meta_app.models import MyBaseModel, UserTypes


class UserManager(BaseUserManager):
    """
    Custom model manager

    Arguments:
        BaseUserManager -- To define a custom manager that extends BaseUserManager
                                providing two additional methods

    Raises:
        TypeError -- It raises if the password is not provided while creating the users.

    Returns:
        user_object -- This will override the default model manager and returns user object.
    """

    def create_user(self, mobile=None, password=None):
        if mobile is None:
            raise TypeError('Users must have mobile number.')

        user = self.model(mobile=mobile, password=password)
        user.set_password(password)
        # user.is_active = True     Defualt value is True
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile, password):
        if password is None:
            raise TypeError('Superusers must have a password.')
        user = self.create_user(mobile=mobile, password=password)
        # user.is_active = True     Defualt value is True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class BaseUser(AbstractBaseUser, PermissionsMixin, MyBaseModel):
    """
    Class to create Custom Auth User Model

    Arguments:
        AbstractBaseUser -- Here we are subclassing the Django AbstractBaseUser,
                                which comes with only three fields:
                                1 - password
                                2 - last_login
                                3 - is_active
                            It provides the core implementation of a user model,
                                including hashed passwords and tokenized password resets.

        PermissionsMixin -- The PermissionsMixin is a model that helps you implement
                                permission settings as-is or
                                modified to your requirements.
    """

    mobile = PhoneNumberField(blank=True,
                              null=True,
                              verbose_name="Mobile Number")

    is_staff = models.BooleanField(default=False)

    is_active = models.BooleanField(default=False)

    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'mobile'
    objects = UserManager()

    class Meta:
        verbose_name = "Base User"
        verbose_name_plural = "Base Users"

    def __str__(self):
        return str(self.mobile)
