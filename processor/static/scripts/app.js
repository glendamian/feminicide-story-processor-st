
function showSpinner(selector) {
  $(selector).html('<div style="text-align:center;"><div class="spinner-border" role="status"><span class="sr-only">Loading...</span></div></div>');
}

function renderStacked(data, selector, title){
    showSpinner(selector);
    // draw a stacked bar chart of above/below threshold story volume by day
    vl.markBar({ tooltip: true, "width": {"band": 0.9} })
    .width(950)
    .data(data)
    .title(title)
    .encode(
      vl.x().fieldT("date").axis({'format': "%m-%d"}),
      vl.y().fieldQ("count"),
      vl.color().fieldN("type"),
      vl.tooltip([vl.fieldT("date"), vl.fieldN("type"), vl.fieldQ("count")])
    )
    .render()
    .then(viewElement => {
        $(selector).html("");
        $(selector).append(viewElement);
    });
}
