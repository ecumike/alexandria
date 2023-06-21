# UXRA metrics

For the most part, this entire site is automated: Every page/template in the metrics app site is fully automated and requires ZERO work from here on out unless you wanted to add features or change the layout/design/whatever. You could leave it alone and it would run itself for years.

Domains, projects, and campaigns are added via the Admin Center. Once a survey campaign is added, you can create a cron job to start pulling responses for that campaign from the survey service you use (Qualtrics, Usabilla, SurveyMonkey, etc) and that project/campaign usually never needs to be touched again. Yearly, quarterly, and domain-level metrics are all automatic from that point.

## Domains and projects
Domains are a way to roll up and organize/group tools and services (projects) into what group/VP/whatever is responsible for them. The key thing about domain is that there are roll-up metrics for a domain so you can see at a glance how a domain is doing with their tools overall. These are calculated nightly after all responses are imported and project snapshots updated. They are stored in the `Domain year snapshot` in the Admin Center.

A `project` is the site, tool, app, or service. Most projects belong to a domain. When they are in a domain they will affect the domain's overall metrics so don't just do it willy-nilly. A project does not have to be in a domain. It can simply be an orphaned project used for metrics reporting.

## Domains list page
This is a simple output of a few fields from each domain's yearly snapshot. A few calcs are done in the view to determine the top-level overall metrics. Basic stuff. Page is fully automated, even at new year.

## Projects list page
The project list page is exactly as named... a list of project based on selected filters. These are NOT contextual. The filters are based on two required selections: `Domain` and `report period`. After that, the filters are based on the snapshot for the project for that period. Ex: Scoring, NPS category, UMUX category.. those are based on the selected quarter snapshot for each project in the selected domain (including "all"). The filters are pretty simple basic since all those fields are stored in the quarter snapshot. That's why the site is so fast. I made it that way. Page is fully automated, even at new year.

## Projects detail page
The project detail page is mostly a report page for a selected quarter report period. If none selected, default is "current score" which is like the latest 90 days "rolling quarter". For the project's given quarter snapshot, some charts are generated with D3 (or C3 helper). Then, a few historical charts are generated from getting a list of the projects snapshots and outputting arrays of #s and quarters, and then using D3 (or C3 helper) project historical charts are generated. This page template is fully automated at this point. Page is fully automated, even at new year.

### Projects detail Time Machine
Normal reporting period selections are by quarter. They product URL param: `reportperiod=<#>q<year>`
URL example: https://someDomain.com/...&project=181&reportperiod=1q2022

Secretly, we also have them by month:
So if `1q2022` means “1st quarter, 2022”…. you can probably guess how to do it by month :)  `<#>m<year>` so change the `reportperiod` in the URL to something like `reportperiod=10m2021` to see reporting for Oct 2021.

Time Machine:
Undocumented feature we have called the Time Machine. It allows you to see reporting for ANY GIVEN DAY in history. For example, let’s say you wanted to see what the NPS scores were on Oct 28, 2021. Meaning… you went back in time and viewed your project detail page on Oct 28. Since this is custom advanced functionality, we put a notice on the page that you are using the Time Machine feature to ensure you are not confused about the data you are seeing.  

To use this feature, instead of using a preset `"month"|"quarter" + year` for the `reportperiod` you would put in an exact date with `<yyyy>-<mm>-<dd>` format.
Example: To see what your project looked like on Oct 28, 2021, you would change the reportperiod URL param to be like this: `reportperiod=2021-10-28`

By default it goes back 90 days from your “reportperiod” date (the date you are pretending to travel back to in time to). 
The second part of this feature is that you can change that default behavior and also set a custom start date. Let’s say you only wanted to see reporting for a 2-week range. You would add a `startdate` param in the same  `<yyyy>-<mm>-<dd>` format. 

So to see your project detail page using data from Oct 14 to Oct 28, you would use the `reportperiod` param, and **add** a custom `startdate` param, so it would be like this: `reportperiod=2021-10-28&startdate=2021-10-14`


## Campaigns
A `campaign` is the way a selected survey is setup and run for a selected project. Projects can have multiple campaigns; a feedback survey campaign, a NPS survey campaign, employee sat survey campaign. Campaigns are your surveys, and they have have responses.

## Quarterly reporting
NPS and UMUX rely on a certain amount of margin of error. Too high and you could be falsely reporting a score that could easily or drastically change with more responses. This mostly relies on the quantity of responses, the more the better. Therefore, we calculate and report scores on a quarterly basis (as opposed to monthly) to ensure we get as many "good enough" scores as possible. To do this, a `quarterly snapshot` is created automatically for every project, for every year, for every quarter that project has a response for. This is the meat-and-potatoes of this whole gig. Calculations can be done nightly on a cron script you setup after all new responses are imported and stored in the quarterly snapshots. Things like response counts, NPS scores, margin of errors, meaningful score dates, the whole deal, are stored in fields. This allows us to have a super fast site and not have to calculate all these numbers on the fly on every page view. That's super inefficient.

## Nightly response imports and quarterly report calculations
You can automate fetching responses from your survey service by setting up a basic Flask app file using APscheduler as a cron that hits your survey service API every nite pulls responses for each of your "active" campaigns.

During the import script, Alexandria keeps track of which projects and which quarters we got responses for. After all responses are imported, a series of calculation scripts are run:

For each project:
 - Update each quarter snapshot we just received a response for (`updateQuarterSnapshot`). This will do a series of date setting and stats calculations (`calculateStats`). It will calculate new NPS, UMUX, and goal completion stats for that quarter for that project
 - Update each domain year-snapshot for each project we touched. This updates the aggregated/roll-up metrics for the domain, based on the projects' snapshots
 
For all projects:
 - Update the "last 90" ("current score") snapshot. This is a rolling 90-180 day snapshot so it gets updated every nite, for every project
 - Now that all snapshots are updated with latest and greatest status, find all active projects that don't have a baseline or target and set the project's current year baseline and target (`setProjectYearBaselinesAndTargets`)
 
 All filters, listings, and graphs are automatically generated based on projects snapshots and stats from snapshots and domain year snapshots. 
 
 After all projects and targets and scores have all been calculated, the domain year snapshot metrics are calculated. These are pretty simply things like counting # of projects in that domain that are above target, that are "excellent", total number projects, etc, etc. Again... stored in a snapshot so we don't have to calculate on-the-fly on every page view.
 
