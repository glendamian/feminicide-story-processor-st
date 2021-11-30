Useful queries for the logging database
=======================================

Connect to db: `dokku postgres:connect mc-story-processor-db`

**Stories fetched by date**

`SELECT date_trunc('day', processed_date) as day, count(*) as stories from stories  group by 1 order by 1  DESC;`

**Stories unprocessed by queued day**

`SELECT date_trunc('day', queued_date) as day, count(*) as stories from stories where processed_date is null group by 1 order by 1  DESC;`

**Stories above/below theshold by day**

`SELECT date_trunc('day', processed_date) as day, above_threshold,  count(*) as stories from stories  group by 1, 2 order by 1  DESC;`
