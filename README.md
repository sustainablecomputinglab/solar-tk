

# Solar-TK: A Data-driven Toolkit for Solar Performance Modeling and Forecasting

Solar-TK is a data-driven toolkit for solar performance modeling and forecasting that is simple, extensible,and publicly accessible. Solar-TK’s simple approach models and forecasts a site’s solar output given only its location and a small amount of historical generation data. Solar- TK’s extensible design includes a small collection of independent modules that connect together to implement basic modeling and forecasting, while also enabling users to implement new energy analytics. 

A key goal of Solar-TK is to be simple to use by researchers that require realistic and accurate solar performance models and forecasts, but are not experts in these areas. 

## Documentation

[Solar-TK Documentation](https://github.com/sustainablecomputinglab/solar-tk/blob/master/docs/manual/)

## Why do we need a toolkit for solar performance modeling and forecasting?

We quote our [Solar-TK paper](http://www.ecs.umass.edu/~irwin/solartk.pdf)
explaining the need for a toolkit:

  > Much of the research work on solar performance modeling and forecasting
  > is not accessible to researchers outside the area, either because it has not 
  > been implemented and released as open source, is too complex and time-consuming to 
  > re-implement, or requires access to proprietary data. 

## What does Solar-TK offer? 

To address the problem, we present Solar-TK, an open data-driven toolkit for solar performance modeling and forecasting that is simple, extensible, and publicly accessible. A key goal of Solar-TK is to be simple to use by researchers that require realistic and accurate solar performance models and forecasts, but are not experts in these areas.
Solar-TK includes:

-  a dataset of solar power generation and energy consumption across hudreds of homes
-  a module to estimate the physical specifications of a solar site, i.e. capacity, tilt, orientation
-  a module to estimate the maximum generation potential of a solar site
-  a module to estimate the weather-adjusted generation for a solar site
-  a module to adjust the estimated output for shading by nearby buildings and trees (will be added in future)
-  a module providing metrics used in solar modeling and forecasting (will be added in future)

# Publications

Find our [Solar-TK paper](http://www.ecs.umass.edu/~irwin/solartk.pdf). Please consider citing our paper if you use Solar-TK in an academic work. 

The BibTex citation is given below. 

@inproceedings{bashir2019solar,  
  title={Solar-TK: A Data-driven Toolkit for Solar PV Performance Modeling and Forecasting},  
  author={Bashir, Noman and Chen, Dong and Irwin, David and Shenoy, Prashant},  
  booktitle={Proceedings of the 16th International Conference on Mobile Ad-hoc and Smart Systems (MASS’19)},  
  year={2019}  
}  

Solar-TK combines a number of insights from prior research listed below. 
 
**Staring at the Sun: A Physical Black-box Solar Performance Model**  
Dong Chen and David Irwin  
BuildSys 2018  
Link: http://www.ecs.umass.edu/~irwin/staring.pdf  

**SunDance: Black-box Behind-the-Meter Solar Disaggregation**  
Dong Chen and David Irwin  
e-Energy 2017  
Link: http://www.ecs.umass.edu/~irwin/e-energy17.pdf

**Black-box Solar Performance Modeling: Comparing Physical, Machine Learning, and Hybrid Approaches**  
Dong Chen and David Irwin  
Greenmetrics 2017  
Link: http://www.ecs.umass.edu/~irwin/greenmetrics17.pdf


Please note that Solar-TK will evolve based on community feedback! Please use the
[online docs](https://github.com/sustainablecomputinglab/solar-tk/docs/manual/)
instead of the paper.


# Solar-TK Help and Resources

* The users are encouraged to use stackoverflow with #solar-tk to get community help. 
* You can also email to Noman Bashir at nbashir@umass.edu for help. Please be patient as it may take a few hours to a day to respond. 

