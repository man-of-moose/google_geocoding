---
title: "606 Final Project"
author: "Alec"
date: "12/2/2021"
output: 
  prettydoc::html_pretty:
    theme: cosmo
    highlight: github
    keep_md: true
    toc: true
    toc_depth: 2
    df_print: paged
---



# Load Packages


```r
library(tidyverse)
library(psych)
library(stringr)
library(ggmap)
library(readr)
```

# Load and Process Data

## Original Post Office Data

Original dataset, post first-round geocoding, contains all 249 post offices in NYC (5 Boroughs).


```r
location_data <- read_csv("data/post_office_coords.csv", show_col_types = FALSE)
```

## Manufactured Routes Dataset

After randomizing the rows of the above address dataset, I created every combination of 2 addresses without repetition. This requires the assumption that the travel duration between any two points in the city is the same in both directions (which is likely not the case). The reason for this decision is due to financial limitations of google maps API (gmaps), which was used to compute the travel distance and duration for each combinatin of addresses. gmaps provides users with a generous amount of free queries after signup, but as it is my personal account I did not want to cross the free-threshold.

In total there are 30,876 route combinations used in the subsequent analysis.


```r
data <- read_csv("data/route_data.csv", show_col_types = FALSE)
```

## Data Cleaning and Additional Feature Engineering

There are instances where different post offices operated in separate units of the same building. In these situations the geodesic distance calculated with geopy and the google_duration provided by gmaps would equal 0, which should not be included in the model.


```r
data <- data %>%
  filter(
    google_duration > 300
  )
```

In addition to the is_same_borough feature which was created using python, here I create a function that will extract an address' zip code, later to be used to create is_same_zip feature for a route


```r
extract_zip <- function(address) {
  zip <- str_extract(address, "\\d{5}")
  
  return(zip)
}
```

Additionally, since we have the data, we should test to see if adding a categorical value designating which two boroughs were involved in a given route will provide value to a model.


```r
get_borough_path <- function(path_string) {
  split <- unlist(str_split(path_string,","))
  b1 <- split[1]
  b2 <- split[2]
  b_vector <- c(b1, b2)
  sorted <- sort(b_vector)
  return(str_c(sorted, collapse=","))
}
```



```r
borough_paths <- lapply(str_c(data$origin_borough, data$destination_borough, sep=","), get_borough_path)
```



```r
data <- data %>%
  mutate(
    origin_zip = extract_zip(origin_address),
    destination_zip = extract_zip(destination_address),
    is_same_zip = origin_zip == destination_zip,
    borough_path = unlist(borough_paths),
    log_norm_geodesic = scale(log(geodesic_distance),center=TRUE, scale=TRUE)
  ) %>%
  select(origin_address, 
         origin_zip,
         origin_borough, 
         origin_coordinate,
         destination_address,
         destination_zip,
         destination_borough,
         destination_coordinate,
         is_same_zip,
         is_same_borough,
         borough_path,
         geodesic_distance,
         log_norm_geodesic,
         google_distance,
         google_duration)
```

# EDA and Data Visualization

## Address Dataset

The routes dataset is based on the initial address dataset, which includes 249 post office addresses in teh 5 boroughs of NYC.


```r
location_data %>%
  ggplot() +
  geom_bar(aes(x=Borough, fill=Borough)) +
  theme(legend.position = "none")
```

![](final_project_files/figure-html/unnamed-chunk-9-1.png)<!-- -->

### Generating map plot

Below we create two functions that extract the latitude and longitude from the initial address dataset (Coordinate was saved as a string).


```r
extract_lat <- function(coordinate_string) {
  lat <- unlist(str_split(str_replace_all(coordinate_string,"\\(?\\)?",""),","))[1]
  
  return(lat)
}
```


```r
extract_long <- function(coordinate_string) {
  long <- unlist(str_split(str_replace_all(coordinate_string,"\\(?\\)?",""),","))[2]
  
  return(long)
}
```


```r
lat_data = lapply(location_data$Coordinate, extract_lat)
long_data = lapply(location_data$Coordinate, extract_long)
```

Next we create another dataframe in the correct format for gmaps


```r
coord_data <- location_data %>%
  select(
    Address,
    Coordinate
  ) %>%
  mutate(
    lat = as.numeric(unlist(lat_data)),
    long = as.numeric(unlist(long_data))
  ) %>%
  select(
    Address,
    lat,
    long
  )
```



```r
api_key <- read_csv("key_file.csv", show_col_types = FALSE)$key[1]
```


```r
register_google(key = api_key)
```



```r
nymap <- get_map(location = c(lon = mean(coord_data$long), lat = mean(coord_data$lat)), zoom = 10,
                      maptype = "satellite", scale = 2)
```


```r
ggmap(nymap) +
  geom_point(data = coord_data, aes(x = long, y = lat, fill = "red", alpha = 0.8), size = 2, shape = 21) +
  guides(fill=FALSE, alpha=FALSE, size=FALSE)
```

```
## Warning: `guides(<scale> = FALSE)` is deprecated. Please use `guides(<scale> =
## "none")` instead.
```

![](final_project_files/figure-html/unnamed-chunk-17-1.png)<!-- -->


## Routes Dataset


```r
describe(data$google_duration)
```

<div data-pagedtable="false">
  <script data-pagedtable-source type="application/json">
{"columns":[{"label":[""],"name":["_rn_"],"type":[""],"align":["left"]},{"label":["vars"],"name":[1],"type":["dbl"],"align":["right"]},{"label":["n"],"name":[2],"type":["dbl"],"align":["right"]},{"label":["mean"],"name":[3],"type":["dbl"],"align":["right"]},{"label":["sd"],"name":[4],"type":["dbl"],"align":["right"]},{"label":["median"],"name":[5],"type":["dbl"],"align":["right"]},{"label":["trimmed"],"name":[6],"type":["dbl"],"align":["right"]},{"label":["mad"],"name":[7],"type":["dbl"],"align":["right"]},{"label":["min"],"name":[8],"type":["dbl"],"align":["right"]},{"label":["max"],"name":[9],"type":["dbl"],"align":["right"]},{"label":["range"],"name":[10],"type":["dbl"],"align":["right"]},{"label":["skew"],"name":[11],"type":["dbl"],"align":["right"]},{"label":["kurtosis"],"name":[12],"type":["dbl"],"align":["right"]},{"label":["se"],"name":[13],"type":["dbl"],"align":["right"]}],"data":[{"1":"1","2":"30788","3":"1901.97","4":"723.1337","5":"1837","6":"1876.231","7":"736.8522","8":"306","9":"4409","10":"4103","11":"0.3294473","12":"-0.3167303","13":"4.12124","_rn_":"X1"}],"options":{"columns":{"min":{},"max":[10]},"rows":{"min":[10],"max":[10]},"pages":{}}}
  </script>
</div>
From the below histogram the response variable 'google_duration' (how long google estimates a trip between two points will tage) is normally distributed with a mean of 1897.7 and a standard deviation of 727.13


```r
data %>%
  ggplot() +
  geom_histogram((aes(x=google_duration)))
```

![](final_project_files/figure-html/unnamed-chunk-19-1.png)<!-- -->


```r
describe(data$geodesic_distance)
```

<div data-pagedtable="false">
  <script data-pagedtable-source type="application/json">
{"columns":[{"label":[""],"name":["_rn_"],"type":[""],"align":["left"]},{"label":["vars"],"name":[1],"type":["dbl"],"align":["right"]},{"label":["n"],"name":[2],"type":["dbl"],"align":["right"]},{"label":["mean"],"name":[3],"type":["dbl"],"align":["right"]},{"label":["sd"],"name":[4],"type":["dbl"],"align":["right"]},{"label":["median"],"name":[5],"type":["dbl"],"align":["right"]},{"label":["trimmed"],"name":[6],"type":["dbl"],"align":["right"]},{"label":["mad"],"name":[7],"type":["dbl"],"align":["right"]},{"label":["min"],"name":[8],"type":["dbl"],"align":["right"]},{"label":["max"],"name":[9],"type":["dbl"],"align":["right"]},{"label":["range"],"name":[10],"type":["dbl"],"align":["right"]},{"label":["skew"],"name":[11],"type":["dbl"],"align":["right"]},{"label":["kurtosis"],"name":[12],"type":["dbl"],"align":["right"]},{"label":["se"],"name":[13],"type":["dbl"],"align":["right"]}],"data":[{"1":"1","2":"30788","3":"15.42192","4":"8.641715","5":"14.59432","6":"14.75174","7":"8.427337","8":"0.3204126","9":"55.11545","10":"54.79504","11":"0.7978277","12":"0.8292887","13":"0.04925034","_rn_":"X1"}],"options":{"columns":{"min":{},"max":[10]},"rows":{"min":[10],"max":[10]},"pages":{}}}
  </script>
</div>
Unlike 'google_duration', the primary independent variable 'geodesic_distance' has a clear right skew and potentially breaches assumption of normality.

The Shapiro test confirms non-normality with a p-value close to zero.



```r
shapiro.test(sample(data$geodesic_distance,100))
```

```
## 
## 	Shapiro-Wilk normality test
## 
## data:  sample(data$geodesic_distance, 100)
## W = 0.93477, p-value = 9.376e-05
```


```r
data %>%
  ggplot() +
  geom_histogram((aes(x=geodesic_distance)))
```

![](final_project_files/figure-html/unnamed-chunk-22-1.png)<!-- -->


```r
qqnorm(data$geodesic_distance)
qqline(data$geodesic_distance)
```

![](final_project_files/figure-html/unnamed-chunk-23-1.png)<!-- -->
Let's test if the log is any better


```r
data %>%
  ggplot() +
  geom_histogram((aes(x=log_norm_geodesic)))
```

![](final_project_files/figure-html/unnamed-chunk-24-1.png)<!-- -->

It seems that the log is not much better than standard geodesic_distance.




```r
qqnorm(data$log_norm_geodesic)
qqline(data$log_norm_geodesic)
```

![](final_project_files/figure-html/unnamed-chunk-25-1.png)<!-- -->

```r
shapiro.test(sample(data$log_norm_geodesic,100))
```

```
## 
## 	Shapiro-Wilk normality test
## 
## data:  sample(data$log_norm_geodesic, 100)
## W = 0.96046, p-value = 0.004335
```

Let's see if we can see a significant effect on the response based on different 'borough_paths'


```r
data %>%
  ggplot() +
  geom_point(aes(x=geodesic_distance, y=google_duration)) +
  facet_wrap(~borough_path)
```

![](final_project_files/figure-html/unnamed-chunk-27-1.png)<!-- -->


```r
data %>%
  ggplot() + 
  geom_boxplot(aes(x=google_duration, y=borough_path), fill="purple")
```

![](final_project_files/figure-html/unnamed-chunk-28-1.png)<!-- -->

# Perform ANOVA test

```r
anova <- aov(google_duration ~ borough_path, data = data)

summary(anova)
```

```
##                 Df    Sum Sq   Mean Sq F value Pr(>F)    
## borough_path    14 9.100e+09 649987339    2858 <2e-16 ***
## Residuals    30773 6.999e+09    227452                   
## ---
## Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1
```


```r
# Following this F Test, we confirm that the 'borough_path' has a significant impact on the ultimate google_duration and that this variable should be retaiend in our model.
```


# Create Linear Model

## Baseline model using just geodesic distance


```r
baseline = lm(google_duration ~ geodesic_distance, data=data)
```


```r
summary(baseline)
```

```
## 
## Call:
## lm(formula = google_duration ~ geodesic_distance, data = data)
## 
## Residuals:
##      Min       1Q   Median       3Q      Max 
## -1218.15  -255.95   -45.47   214.78  1604.54 
## 
## Coefficients:
##                   Estimate Std. Error t value Pr(>|t|)    
## (Intercept)       778.6676     4.1503   187.6   <2e-16 ***
## geodesic_distance  72.8380     0.2348   310.2   <2e-16 ***
## ---
## Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1
## 
## Residual standard error: 356 on 30786 degrees of freedom
## Multiple R-squared:  0.7577,	Adjusted R-squared:  0.7577 
## F-statistic: 9.625e+04 on 1 and 30786 DF,  p-value: < 2.2e-16
```

Interpreting the above, we can write out the following linear model:

google_duration = 772.8249 + 73.1228*geodesic_distance

Intercept: assuming geodesic_distance of 0, the google_duration will be roughly 773 seconds

Slope: for each additinal km added to geodesic distance, we can expect that google_duration will increase be roughly 73 seconds.

## Baseline log



```r
log_model = lm(google_duration ~ log_norm_geodesic, data=data)
```


```r
summary(log_model)
```

```
## 
## Call:
## lm(formula = google_duration ~ log_norm_geodesic, data = data)
## 
## Residuals:
##     Min      1Q  Median      3Q     Max 
## -997.32 -300.78  -21.85  266.35 1669.34 
## 
## Coefficients:
##                   Estimate Std. Error t value Pr(>|t|)    
## (Intercept)        1901.97       2.23   853.0   <2e-16 ***
## log_norm_geodesic   608.15       2.23   272.7   <2e-16 ***
## ---
## Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1
## 
## Residual standard error: 391.3 on 30786 degrees of freedom
## Multiple R-squared:  0.7073,	Adjusted R-squared:  0.7073 
## F-statistic: 7.438e+04 on 1 and 30786 DF,  p-value: < 2.2e-16
```


## Adding additional features


```r
feature_model = lm(google_duration ~ poly(geodesic_distance,1) + is_same_zip + borough_path, data=data)
```


```r
summary(feature_model)
```

```
## 
## Call:
## lm(formula = google_duration ~ poly(geodesic_distance, 1) + is_same_zip + 
##     borough_path, data = data)
## 
## Residuals:
##     Min      1Q  Median      3Q     Max 
## -1106.1  -203.8   -16.3   184.8  1422.2 
## 
## Coefficients:
##                                           Estimate Std. Error t value Pr(>|t|)
## (Intercept)                               1643.330     10.098 162.742  < 2e-16
## poly(geodesic_distance, 1)              102094.215    484.794 210.593  < 2e-16
## is_same_zipTRUE                           -359.860     38.426  -9.365  < 2e-16
## borough_pathBronx,Brooklyn                 325.742     12.677  25.695  < 2e-16
## borough_pathBronx,Manhattan                 60.776     11.407   5.328 1.00e-07
## borough_pathBronx,Queens                   -14.589     11.686  -1.248    0.212
## borough_pathBronx,Staten Island            295.750     17.859  16.560  < 2e-16
## borough_pathBrooklyn,Brooklyn              353.716     11.924  29.665  < 2e-16
## borough_pathBrooklyn,Manhattan             567.055     11.088  51.139  < 2e-16
## borough_pathBrooklyn,Queens                364.738     11.247  32.430  < 2e-16
## borough_pathBrooklyn,Staten Island         433.577     14.199  30.535  < 2e-16
## borough_pathManhattan,Manhattan             80.746     11.824   6.829 8.72e-12
## borough_pathManhattan,Queens               220.075     11.174  19.695  < 2e-16
## borough_pathManhattan,Staten Island        520.086     14.805  35.129  < 2e-16
## borough_pathQueens,Queens                   65.196     11.867   5.494 3.96e-08
## borough_pathQueens,Staten Island           393.513     15.839  24.845  < 2e-16
## borough_pathStaten Island,Staten Island     -7.474     29.746  -0.251    0.802
##                                            
## (Intercept)                             ***
## poly(geodesic_distance, 1)              ***
## is_same_zipTRUE                         ***
## borough_pathBronx,Brooklyn              ***
## borough_pathBronx,Manhattan             ***
## borough_pathBronx,Queens                   
## borough_pathBronx,Staten Island         ***
## borough_pathBrooklyn,Brooklyn           ***
## borough_pathBrooklyn,Manhattan          ***
## borough_pathBrooklyn,Queens             ***
## borough_pathBrooklyn,Staten Island      ***
## borough_pathManhattan,Manhattan         ***
## borough_pathManhattan,Queens            ***
## borough_pathManhattan,Staten Island     ***
## borough_pathQueens,Queens               ***
## borough_pathQueens,Staten Island        ***
## borough_pathStaten Island,Staten Island    
## ---
## Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1
## 
## Residual standard error: 304.6 on 30771 degrees of freedom
## Multiple R-squared:  0.8226,	Adjusted R-squared:  0.8225 
## F-statistic:  8920 on 16 and 30771 DF,  p-value: < 2.2e-16
```

The Adjusted R Squared went up a lot!

## Testing out polynomials


```r
poly_model = lm(google_duration ~ poly(geodesic_distance,2) + is_same_zip  + borough_path, data=data)
```


```r
summary(poly_model)
```

```
## 
## Call:
## lm(formula = google_duration ~ poly(geodesic_distance, 2) + is_same_zip + 
##     borough_path, data = data)
## 
## Residuals:
##    Min     1Q Median     3Q    Max 
## -970.8 -202.2  -15.5  183.5 1396.3 
## 
## Coefficients:
##                                           Estimate Std. Error t value Pr(>|t|)
## (Intercept)                               1725.851      9.913 174.099  < 2e-16
## poly(geodesic_distance, 2)1             100333.215    469.865 213.536  < 2e-16
## poly(geodesic_distance, 2)2             -17659.091    376.655 -46.884  < 2e-16
## is_same_zipTRUE                           -247.442     37.201  -6.651 2.95e-11
## borough_pathBronx,Brooklyn                 223.750     12.439  17.988  < 2e-16
## borough_pathBronx,Manhattan                -50.455     11.273  -4.476 7.64e-06
## borough_pathBronx,Queens                  -138.634     11.595 -11.956  < 2e-16
## borough_pathBronx,Staten Island            496.379     17.777  27.923  < 2e-16
## borough_pathBrooklyn,Brooklyn              322.294     11.539  27.931  < 2e-16
## borough_pathBrooklyn,Manhattan             456.268     10.970  41.592  < 2e-16
## borough_pathBrooklyn,Queens                237.972     11.197  21.253  < 2e-16
## borough_pathBrooklyn,Staten Island         317.540     13.940  22.780  < 2e-16
## borough_pathManhattan,Manhattan             75.335     11.424   6.595 4.34e-11
## borough_pathManhattan,Queens               101.413     11.088   9.146  < 2e-16
## borough_pathManhattan,Staten Island        448.183     14.385  31.156  < 2e-16
## borough_pathQueens,Queens                    2.534     11.542   0.220   0.8262
## borough_pathQueens,Staten Island           430.652     15.322  28.106  < 2e-16
## borough_pathStaten Island,Staten Island    -61.804     28.761  -2.149   0.0317
##                                            
## (Intercept)                             ***
## poly(geodesic_distance, 2)1             ***
## poly(geodesic_distance, 2)2             ***
## is_same_zipTRUE                         ***
## borough_pathBronx,Brooklyn              ***
## borough_pathBronx,Manhattan             ***
## borough_pathBronx,Queens                ***
## borough_pathBronx,Staten Island         ***
## borough_pathBrooklyn,Brooklyn           ***
## borough_pathBrooklyn,Manhattan          ***
## borough_pathBrooklyn,Queens             ***
## borough_pathBrooklyn,Staten Island      ***
## borough_pathManhattan,Manhattan         ***
## borough_pathManhattan,Queens            ***
## borough_pathManhattan,Staten Island     ***
## borough_pathQueens,Queens                  
## borough_pathQueens,Staten Island        ***
## borough_pathStaten Island,Staten Island *  
## ---
## Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1
## 
## Residual standard error: 294.3 on 30770 degrees of freedom
## Multiple R-squared:  0.8345,	Adjusted R-squared:  0.8344 
## F-statistic:  9124 on 17 and 30770 DF,  p-value: < 2.2e-16
```

I am happy with this model. Let's see what the RSME is!


```r
sqrt(sum(poly_model$residuals^2) / length(poly_model$residuals))
```

```
## [1] 294.2121
```

Not bad at all! RSME is 294 seconds, or just under 5 minutes.

294/60




```r
ggplot(data = poly_model, aes(x = .fitted, y = .resid, color=borough_path, alpha=.1)) +
  geom_point() +
  geom_hline(yintercept = 0, linetype = "dashed") +
  xlab("Fitted values") +
  ylab("Residuals")
```

![](final_project_files/figure-html/unnamed-chunk-40-1.png)<!-- -->

```r
poly_model %>%
  ggplot() +
  geom_boxplot(aes(x=.resid, y=borough_path), fill="purple") +
  xlab("Residuals") +
  ylab("Borough Path")
```

![](final_project_files/figure-html/unnamed-chunk-41-1.png)<!-- -->


```r
qqnorm(poly_model$residuals)
qqline(poly_model$residuals)
```

![](final_project_files/figure-html/unnamed-chunk-42-1.png)<!-- -->


```r
ggplot() +
  geom_histogram(aes(x=poly_model$residuals))
```

![](final_project_files/figure-html/unnamed-chunk-43-1.png)<!-- -->


```r
data <- data %>%
  mutate(
    predictions = poly_model$fitted.values,
    residuals = poly_model$residuals
  )
```


```r
data %>%
  arrange(desc(residuals))
```

<div data-pagedtable="false">
  <script data-pagedtable-source type="application/json">
  </script>
</div>


2012 / 60




```r
get_address_residual <- function(address){
  in_scope_df <- data%>%
                  filter(
                    origin_address == address | destination_address == address
                  )
  avg_residual = mean(abs(in_scope_df$residuals))
  
  return(avg_residual)
  
}
```



```r
coord_data <- coord_data %>%
  mutate(
    average_residual = unlist(lapply(coord_data$Address, get_address_residual)),
    residual_group = ntile(average_residual, 20))
```



```r
ggmap(nymap) +
  geom_point(data = coord_data, aes(x = long, y = lat, color = residual_group), size = 2, shape = 20, position="jitter") +
  scale_color_gradient(low="green", high="red")
```

![](final_project_files/figure-html/unnamed-chunk-48-1.png)<!-- -->



```r
ggmap(nymap) +
  geom_point(data = coord_data[coord_data$residual_group %in% c(18,19,20),], aes(x = long, y = lat), color = "orange", size = 2, shape = 20, position="jitter")
```

![](final_project_files/figure-html/unnamed-chunk-49-1.png)<!-- -->
Over Predictions
14506 243rd St, Rosedale, NY 11422
626 Sheepshead Bay Rd Ste 8, Brooklyn, NY 11224

Under Predictions
45 Bay St Ste 2, Staten Island, NY 10301
1369 Broadway, Brooklyn, NY 11221



```r
under_predictions <- coord_data %>%
  mutate(
    type = "under"
  ) %>%
  filter(
    str_detect(Address, "45 Bay St Ste 2") | str_detect(Address, "1369 Broadway")
  )
```


```r
over_predictions <- coord_data %>%
  mutate(
    type = "over"
  ) %>%
  filter(
    str_detect(Address, "14506 243rd St") | str_detect(Address, "626 Sheepshead Bay Rd")
  )
```


```r
bad_predictions <- rbind(over_predictions, under_predictions)
```



```r
ggmap(nymap) +
  geom_point(data = bad_predictions, aes(x = long, y = lat, color = type), size = 2, shape = 20, position="jitter")
```

![](final_project_files/figure-html/unnamed-chunk-53-1.png)<!-- -->