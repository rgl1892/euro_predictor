var margin = { top: 30, right: 50, bottom: 50, left: 30 },
        width = document.getElementById("heat_div").offsetWidth - margin.left - margin.right,
        height = 400 - margin.top - margin.bottom;

var svg = d3.select('#heat_map').append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
      .append('g')
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

async function get_current_filters() {
    var user = document.getElementById('user_select').value;
    var match_choice = document.getElementById('match').value;
    var url = `api/predictions?user=${user}&match_choice__match_number=${match_choice}`;

    svg.selectAll("*").remove();
    svg.append("text").text("Loading")

    var data = await d3.json(url);

    svg.selectAll("*").remove();

    var home = d3.filter(data, d => d.score != null && d.match_choice.home_away == 'Home');
    var away = d3.filter(data, d => d.score != null && d.match_choice.home_away == 'Away');
    var scores = d3.transpose([d3.map(home,d => d.score),d3.map(away,d => d.score)]);
    
    var newArray = [];
    for(var element of scores){
        if(typeof newArray[JSON.stringify(element)] === 'undefined' || newArray[JSON.stringify(element)] === null){
          newArray[JSON.stringify(element)] = 1;
        }else{
          newArray[JSON.stringify(element)] +=1;
        }
      }
      var result = Object.keys(newArray).map(key => ({
        item: JSON.parse(key),
        count: newArray[key]
      }));   

    

    var x = d3.scaleBand()
            .range([0,width])
            .domain([0,1,2,3,4,5,6])
            .padding(0.05);
    svg.append("g")
        .attr("transform", `translate(0, ${height})`)
      .call(d3.axisBottom(x));

    var y = d3.scaleBand()
      .range([height,0])
      .domain([0,1,2,3,4,5,6])
      .padding(0.05);
    svg.append("g")
      .call(d3.axisLeft(y));

    const myColor = d3.scaleSequential(d3.interpolatePlasma)
      .domain([0,d3.max(result,d=>d.count)]);

    svg.append("text")
      .attr("class", "x label")
      .attr("text-anchor", "end")
      .attr("x", width)
      .attr("y", height + 40)
      .text(`${home[0].country}`);
    svg.append("text")
    .attr("class", "y label")
    .attr("text-anchor", "end")
    .attr("y", 6)
    .attr("x", 0)
    .attr("dy", ".75em")
    .attr("transform", "rotate(-90)")
    .text(`${away[0].country}`);

    svg.selectAll()
      .data(result,)
      .join("rect")
      .attr("x", function(d) { return x(d.item[0]) })
      .attr("y", function(d) { return y(d.item[1]) })
      .attr("rx", 4)
      .attr("ry", 4)
      .attr("width", x.bandwidth() )
      .attr("height", y.bandwidth() )
      .style("fill", function(d) { return myColor(d.count)} )
      .append("svg:title")
        .text((d) => `${d.count}`)


    
    




}


document.getElementById('user_select').addEventListener('change',get_current_filters)
document.getElementById('match').addEventListener('change',get_current_filters)


