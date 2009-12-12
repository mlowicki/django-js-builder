"""
"""
from optparse import make_option

from django.core.management.base import BaseCommand, LabelCommand

from js_builder.utils import build_all_packages, build_package


class Command(LabelCommand):

    option_list = BaseCommand.option_list + (
        make_option("-c", "--compress", action="store_true", dest="compress",
            default=False,
            help="Compress JavaScript packages after building process"),)
 
    help = "Build JavaScript packages."

    def handle(self, *labels, **options):
        """
        """
        if not labels:
            build_all_packages(**options)

        for label in labels:
            self.handle_label(label, **options)

    def handle_label(self, label, **options):
        """
        """
        build_package(label, **options)
