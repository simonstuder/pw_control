from setuptools import setup, find_packages
from distutils.util import convert_path

"""
main_ns = {}
ver_path = convert_path('pw_control/__init__.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)
    """

setup(
    name='pw_control',
    version='0.1.0',
    description='Link and Create Pipewire Nodes',
    url='https://github.com/simonstuder/pipewire_python',
    author='Simon Studer',
    author_email='s.studer.s@gmail.com',
    license='',
    packages=['pw_control'],
    install_requires=['setuptools',
                      'numpy',                     
                      ],

    #use_scm_version=True,
    #setup_requires=['setuptools_scm'],

    classifiers=[
        'Development Status :: 1 - Planning',
        #'Intended Audience :: Science/Research',
        #'License :: OSI Approved :: BSD License',  
        'Operating System :: POSIX :: Linux',        
        #'Programming Language :: Python :: 2',
        #'Programming Language :: Python :: 2.7',
        #'Programming Language :: Python :: 3',
        #'Programming Language :: Python :: 3.4',
        #'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.10',
    ],
)
