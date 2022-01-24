# UXRA web site

Mark Wise is the owner of the content for these pages. 

All web site pages are just templates in templates/info. Pretty straight-forward.

The views control what breadcrumb shows up and which left nav is highlighted in the `info/page_template.html` file

## FAQs
FAQs are managed via the Admin Center. In there you setup categories and then create FAQs and select what categories they go/apply to (can be more than 1). HTML pass-thru is setup.

## About us
The "about us" view contains the list of emails. The page simply loops thru them with JS and creates a box for each person with info from the enterprise directory. Fully dynamic/automated.

## Release notes
These are managed via the Admin Center. The dev (Michael) creates a release (just a tag with `R##`) in the repo whenever he's had enough meaningful updates to call it a "release". The release notes are what they are... notes about each tagged release in the repo. Only high-level description is provided so they can be used for the MOR slides.

## What's new
There are like a higher level, more prominent "release notes". These are more like epics, or meaningful updates that we want to make sure users are aware of. This is equivalent to a "latest news" and "important updates you should know about" page. The key thing and difference with these, is that when a new "What's new" is posted every user will get a little toaster notification on the site that there's a new "What's new" news item. Users can also subscribe (on the list page) to email updates so they don't have to visit the site to get notified that a significant update has been made. 
