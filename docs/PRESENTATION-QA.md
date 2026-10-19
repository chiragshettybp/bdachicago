# Presentation Q&A

## What does the dataset contain?

It is the UCI ElectricityLoadDiagrams20112014 dataset: 370 client columns and
15-minute load readings over 2011–2014. Values are kW.

## How is energy calculated?

Each reading covers 15 minutes, so its energy is `kW × 0.25`, or `kW / 4`,
measured in kWh. Daily energy is the sum of those interval energies.

## How are zeroes and missing values treated?

The dataset is described as having no missing values. Preparation rejects blank
or malformed readings but preserves zeroes, including the supplied zero-filled
periods before some clients appear.

## Why use more than one big-data tool?

Python creates a validated common daily input. MongoDB, Hadoop MapReduce, Pig,
and Hive offer different ingestion, storage, processing, and query approaches.
The annual client summaries can be compared to check analytical consistency.

## What is special about daylight saving time?

The file uses Portuguese local time and always has 96 measures per day. Spring
transition values between 1:00 and 2:00 are zero; autumn transition values
aggregate two hours. The workflow preserves those source values and warns
against naive time-of-day comparisons around the transition.
