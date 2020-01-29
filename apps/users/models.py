from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from django.db import models
from django.core.validators import MaxValueValidator

from apps.meta_app.models import MyBaseModel, UserTypes
from phonenumber_field.modelfields import PhoneNumberField


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

    def create_user(self, email, password=None):
        if email is None:
            raise TypeError('Users must have an email address.')

        user = self.model(email=email, password=password)
        user.set_password(password)
        # user.is_active = True     Defualt value is True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        if password is None:
            raise TypeError('Superusers must have a password.')
        user = self.create_user(email=email, password=password)
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
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Others', 'Others')
    )

    email = models.EmailField(blank = True, null = True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    first_name = models.CharField(max_length=50,
                                  blank=False,
                                  null=False,
                                  verbose_name='First Name')

    last_name = models.CharField(max_length=50,
                                 blank=True,
                                 null=True,
                                 verbose_name='Last Name')

    middle_name = models.CharField(max_length=50,
                                   blank=True,
                                   null=True,
                                   verbose_name='Middle Name')

    mobile = PhoneNumberField(blank=True,
                              null=True,
                              verbose_name="Mobile Number")

    otp = models.CharField(blank = True,
                           null=True,
                           max_length=4,
                           verbose_name="Otp Number")

    facebook_id = models.CharField(blank = True,
                           null=True,
                           max_length=100,
                           verbose_name="Facebook Id")

    google_id = models.CharField(blank = True,
                           null=True,
                           max_length=100,
                           verbose_name="Google Id")

    otp_generate_time = models.DateTimeField(blank = True,
                                       null=True,
                                       auto_now_add=True,
                                       verbose_name="otp generate time")

    # display_picture = models.ImageField(upload_to=generate_display_picture_path,
    # storage=MediaStorage(),
    # validators=[validate_file_size, ],
    # blank=True,
    # null=True,
    # verbose_name='Profile Picture')

    gender = models.CharField(choices=GENDER_CHOICES,
                              blank=True,
                              null=True,
                              max_length=6,
                              verbose_name='Gender')

    age = models.IntegerField(blank=True, null=True)

    address = models.TextField(blank=True, null=True)

    mobile_verified = models.BooleanField(default=False,
                                         verbose_name='Mobile Verified')

    user_types = models.ManyToManyField(UserTypes)

    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'

    objects = UserManager()

    class Meta:
        verbose_name = "Base User"
        verbose_name_plural = "Base Users"

    def __str__(self):
        return str(self.mobile)
