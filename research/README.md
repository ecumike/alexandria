# UXRA research library

Research artifacts are available to anyone and anyone can create them. The only people that can edit them are creators or selected "additional editors". LUX admins have full access to everything in LUX. Example diagram:

<img src="../docs/access-control.png?raw=true" alt="Access diagram" width="600">

The research home is a list of all artifacts with facets/filters. Filters are dynamically generated based on the found result set, meaning they are contextual to the results that are currently showing.

Artifacts are also searchable. Search is a straight search on certain fields in the research artifact. There is no weighting, no relevance/scoring nor "best matches". It's straight "here's results that contain your text".

## Research form
The research form is pretty straight forward, with some JS on there to show/hide fields based on the selected "status". For example if it's not completed, you won't see fields for findings and the research date. There are a few taxonomy items, like status and types, etc. Those are all managed in the Admin Center in the Website/Research section.

## Research detail page
The detail page is pretty basic. Some HTML pass-thru is allowed, and a "notify of broken link" feature is setup. Because a lot of items are in Box and permissions aren't set correctly and we can't control them, this allows users to flag links that are no longer working so they can be fixed, or removed, or whatever. We now have COS (Cloud object storage) setup and users can upload files and we store them. This removes the dependency on Box and prevents issues like improper Box link/file permissions.

## Search
Search is a straight Django multi-field search. There is no relevance or "similar to" feature results because frankly it's extra work that has yet to be requested or needed. Finding research isn't a problem.

## Search filters
Facets (filters) on the left work just like Amazon: They are contextual to the currently showing results/list of research. Basic JS triggers the form onchange of any filter. Filters are taxonomy lists/items that are managed in the Admin Center in the Website/Research section.
