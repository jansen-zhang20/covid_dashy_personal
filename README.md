# covid_dashy_personal
This is a personal project to build a simple COVID-19 tracker for Australia with Dash.

Key functions of this dashy will be to
* Display daily trend in COVID-19 cases over recent period
* Compute simple projection of cases, by estimating the current effective reproduction rate (R_eff) and assuming continued growth at this rate
* Toggle view between key states
* Specify custom values of R_eff to provide simple scenario modelling

Potential development
* More refined estimate of R_eff by applying additional smoothing to data
* Compute confidence interval around R_eff and display prediction range
* More refined projections with non-constant R_eff
* Pre-built scenarios to select
