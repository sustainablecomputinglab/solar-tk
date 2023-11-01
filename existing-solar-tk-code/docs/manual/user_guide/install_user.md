# Installing Solar-TK

As a first step, please fork the Solar-TK git repository and navigate to the main folder. We are working on making it available on python packages. 

We recommend using [Anaconda](https://store.continuum.io/cshop/anaconda/), which bundles together most of the required packages. Solar-TK requires Python 3.6+ due to the module it depends upon.

After Anaconda has been installed, open up the terminal (Unix) or Anaconda prompt (Windows):

1.  Solar-TK should work fine in the base environment, but we recommend creating a new environment where Solar-TK and related dependecies are installed.

	```bash
	conda create --name solartk-env 
	```

2. Activate the new *solartk-env* environment.

	```bash
	conda activate solartk-env
	```

4. From the main folder, install the requirements.

	```bash
	pip install -r requirements.txt
	```

5. From the main folder, run the following command.

	```bash
	chmod +x solartk/*.py
	```

6. Users can use the modules with absolute paths now. A script to set global paths will be added soon.
	```bash
	path_to_folder/solar-tk/solartk/module_name.py
	```
Please refer to the [Hello World Example](https://github.com/sustainablecomputinglab/solar-tk/blob/master/docs/manual/user_guide/hello_world.md). 

7. To deactivate this environment,

	```bash
	conda deactivate
	```
    
We recommend checking the [Anaconda documentation about environments](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) if the concept is new to you.

