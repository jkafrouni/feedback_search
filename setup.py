from setuptools import setup

setup(name='feedback_search',
      version='0.1',
      description="Information retrieval system that exploits user-provided relevance feedback to improve the search results returned by Google.",
      author='Jerome Kafrouni',
      author_email='j.kafrouni@columbia.edu',
      url='https://github.com/jkafrouni',
      packages=['feedback_search'],
      install_requires=[
          # add here any tool that you need to install via pip 
          # to have this package working
          'google-api-python-client',
      ],
      entry_points={
          'console_scripts': [
              'run = feedback_search.__main__:main'
          ]
      },
)