# Research library

Research artifacts are available to anyone and anyone can create them. The only people that can edit them are creators or selected "additional editors". Admins have access to everything.

The research home is a list of all artifacts with facets/filters. Filters are dynamically generated based on the found result set, meaning they are contextual to the results that are currently showing.

Research meta data is searchable. Search is a straight search on certain fields in the research artifact. There is no weighting, relevance, scoring nor "best matches". It's straight "here's results that contain your text".

## Research form
The research form is pretty straight forward, with some JS on there to show/hide fields based on the selected "status". If it's not completed, you won't see fields for findings and the research date. There are a few taxonomy items like status and types, etc. Those are all managed in the Admin Center in the Research section.

## Research detail page
The detail page is pretty basic. Some HTML pass-thru is allowed, and a "notify of broken link" feature is setup which allows users to flag links that are no longer working so they can be fixed, or removed, or whatever. You can also use COS (Cloud object storage) setup and have users upload files and store them. This removes the dependency on 3rd party file host systems (Dropbox, Google Drive, Box, etc) and prevents permission and "file removed" issues.

## Search
Search is a straight Django multi-field search. 

## Search filters
Facets (filters) on the left work just like Amazon: They are contextual to the currently showing results/list of research. JS triggers the form onchange of any filter. Filters are taxonomy lists that are managed in the Admin Center.
