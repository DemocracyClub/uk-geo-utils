# Generated by Django 2.0.8 on 2020-01-31 15:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("uk_geo_utils", "0007_remove_onsud_ctry_flag")]

    operations = [
        migrations.AddField(
            model_name="address",
            name="addressbase_postal",
            field=models.CharField(default="D", max_length=1),
            preserve_default=False,
        )
    ]
