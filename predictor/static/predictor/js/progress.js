var margin = { top: 30, right: 50, bottom: 50, left: 30 },
        width = document.getElementById("patriot_div").offsetWidth - margin.left - margin.right,
        height = 400 - margin.top - margin.bottom;

var svg = d3.select('#patriot_map').append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
      .append('g')
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

async function get_current_filters() {
    var user = document.getElementById('user_select').value;
    var url = `/api/predictions?user=${user}`;

    svg.selectAll("*").remove();
    svg.append("text").text("Loading")

    var data = await d3.json(url);

    svg.selectAll("*").remove();

    
}

document.getElementById('user_select').addEventListener('change',get_current_filters);