"""

"""
from optparse import make_option

from django.core.management.base import BaseCommand, NoArgsCommand

from js_builder.utils import build_all_packages

class Command(NoArgsCommand):
    option_list = BaseCommand.option_list + (
        make_option("-c", "--compress", action="store_true", dest="compress",
            default=False,
            help="Compress JavaScript packages after building process"),)

    help = "Build JavaScript packages."

    def handle_noargs(self, **options):
        build_all_packages()
