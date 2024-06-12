var margin = { top: 30, right: 50, bottom: 50, left: 30 },
        width = document.getElementById("heat_div").offsetWidth - margin.left - margin.right,
        height = 400 - margin.top - margin.bottom;

var svg = d3.select('#goals_map').append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
      .append('g')
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

async function get_current_filters() {
    var user = document.getElementById('user_select_goals').value;
    var url = `api/predictions?user=${user}`;

    console.log(url)
}


document.getElementById('user_select').addEventListener('change',get_current_filters)