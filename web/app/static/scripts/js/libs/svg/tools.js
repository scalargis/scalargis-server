var insertLinebreaks = function (d) {
    var el = d3.select(this);
    var words = d.split(' ');
    el.text('');

    for (var i = 0; i < words.length; i++) {
        var tspan = el.append('tspan').text(words[i]);
        if (i > 0)
            tspan.attr('x', 0).attr('dy', '15');
    }
};



function generate_dendro_pdm(rec){
    console.log("running graph...");
        var svg = d3.select("svg"),
            width = +svg.attr("width"),
            height = +svg.attr("height"),
            g = svg.append("g").attr("transform", "translate(80,0)");

        var root = d3.stratify()
            .id(function(d) { return d.name; })
            .parentId(function(d) { return d.parent; })
            (rec);

        var tree = d3.cluster()
            .size([height, width - 300]);

        tree(root);

var link = g.selectAll(".link")
      .data(root.descendants().slice(1))
    .enter().append("path")
      .attr("class", "link")
      .style("stroke-width",3)
      .attr("d", function(d) {
        return "M" + d.y + "," + d.x
            + "C" + (d.parent.y + 100) + "," + d.x
            + " " + (d.parent.y + 100) + "," + d.parent.x
            + " " + d.parent.y + "," + d.parent.x;
      });

  var node = g.selectAll(".node")
      .data(root.sum(function(d) { return d.value/10000000; }).descendants())
    .enter().append("g")
      .attr("class", function(d) { return "node" + (d.children ? " node--internal" : " node--leaf"); })
      .attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; });

  node.append("circle")
      //.attr("r", function(d){ return d.leaves().length + 2;});
      //.attr("r", function(d){return d.data.value + 2;});
      .attr("r", function(d){return d.value;}); // grace a root.sum

  node.append("text")
      .attr("dy", function(d) { return d.children ? 13 : 3; })
      .attr("x", function(d) { return d.children ? -8 : 8; })
      .style("text-anchor", function(d) { return d.children ? "middle" : "start"; })
      .text(function(d) {
                txt = d.id.length>9 ? d.id.substring(0,d.id.length-3) : d.id;
                txt = txt.length>33 ? txt.substring(0,30)+"..." : txt;
                return txt
            });



    }



function log_linechart(rec){

    //var svg = d3.select("svg"),
    var svg = d3.select("#chart_line").append("svg")
        .attr("width", 500)
        .attr("height", 300)

     var  margin = {top: 40, right: 20, bottom: 50, left: 50},
        width = +svg.attr("width") - margin.left - margin.right,
        height = +svg.attr("height") - margin.top - margin.bottom,
        g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var parseTime = d3.timeParse("%Y-%m-%d");


    var x = d3.scaleTime()
        .rangeRound([0, width]);

    var y = d3.scaleLinear()
        .rangeRound([height, 0]);


    //var xx = d3.scaleBand().rangeRound([0, width]).padding(0.1);

    var line0 = d3.line()
        .x(function(d) {
            return x(d.date); })
        .y(function(d) {
            return y(0); });

    var line = d3.line()
        .x(function(d) {
            return x(d.date); })
        .y(function(d) {
            return y(d.count); });


    var line_vm = d3.line()
        .x(function(d) {
            return x(d.date); })
        .y(function(d) {
            return y(d.vm); });

    rec.forEach(function(d) {
          d.date = parseTime(String(d.date));
          d.count = +d.count;
      });


      x.domain(d3.extent(rec, function(d) { return d.date; }));
      //y.domain(d3.extent(rec, function(d) { return d.count; }));
      max_y = d3.max(rec, function(d) { return d.count; });
      y.domain([0,max_y]);


      g.append("g")
          .attr("class", "axis axis--x")
          .attr("transform", "translate(0," + height + ")")
          .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%d-%m-%y")))
          .selectAll("text")
            .style("text-anchor", "end")
            .attr("dx", "-.8em")
            .attr("dy", ".15em")
            .attr("transform", "rotate(-60)" );

      g.append("g")
          .attr("class", "axis axis--y")
          .call(d3.axisLeft(y))
        .append("text")
          .attr("fill", "#000")
          .attr("transform", "rotate(-90)")
          .attr("y", 6)
          .attr("dy", "0.71em")
          .style("text-anchor", "end")
          .text("Total de Operações");

     g.selectAll("dot")
        .data(rec)
      .enter().append("circle")
        .attr("r", 2.5)
        .attr("cx", function(d) { return x(d.date); })
        .attr("cy", function(d) { return y(0); })
        .style("fill", "#ff3737")
        .style("opacity",0)
        .transition()
            .duration(2000)
            .style("opacity",1)
            .attr("cy", function(d) { return y(d.count); });

      g.append("path")
          //.datum(rec)
          .attr("class", "line")
          .attr("d", line0(rec))
          .style('stroke-width', 2)
          .style('stroke', 'red')
          .style("opacity",0)
          .transition()
            .duration(2000)
            .style("opacity",1)
            .attr("d", line(rec));


        g.append("text")
                .attr("id", "center_text2")
                .style("fill", "black")
                .style("font-size", "14px")
                .attr("dy", ".25em")
                .attr("text-anchor", "left")
                .attr("y", -20)
                .attr("x", 60)
                .text("Operações efectuadas nos últimos " + rec.length + " dias");

/*      g.append("path")
          //.datum(rec)
          .attr("class", "line")
          .attr("d", line0(rec))
          .style('stroke-width', 2)
          .style('stroke', 'blue')
          .style("opacity",0)
          .transition()
            .duration(2000)
            .style("opacity",1)
            .attr("d", line_vm(rec))
          .delay(1000);
*/
/*          g.selectAll(".bar")
            .data(rec)
            .enter().append("rect")
              .attr("class", "bar")
              //.attr("x", function(d) { return x(d.date);})
              .attr("x", function(d) { return x(d.date) - (width/rec.length)/2; })
              .attr("y", function(d) { return y(d.count); })
              //.attr("width", xx.bandwidth())
              .attr("width", width/rec.length)
              .attr("height", function(d) { return height - y(d.count); });*/


  }

  function log_barchart(rec){
    rec = rec.slice(-15);
    var svg = d3.select("svg"),
        margin = {top: 40, right: 20, bottom: 50, left: 50},
        width = +svg.attr("width") - margin.left - margin.right,
        height = +svg.attr("height") - margin.top - margin.bottom,
        g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var parseTime = d3.timeParse("%Y-%m-%d");


    //var x = d3.scaleTime().rangeRound([0, width]);

    var x = d3.scaleTime().range([width/rec.length/2, width-width/rec.length/2]);
    //x.ticks(d3.timeDay.every(1));

    var y = d3.scaleLinear()
        .rangeRound([height, 0]);

    var z = d3.scaleOrdinal()
        .range(["#337ab7", "#f0ad4e", "#5cb85c"]);

    var stack = d3.stack();

    rec.forEach(function(d) {
          d.date = parseTime(String(d.date));
          d.count = +d.count;
          d.vm = +d.vm;
          d.ap = +d.ap;
          d.ep = +d.ep;
      });


      x.domain(d3.extent(rec, function(d) { return d.date; }));
      //y.domain(d3.extent(rec, function(d) { return d.count; }));
      max_y = d3.max(rec, function(d) { return d.count; });
      y.domain([0,max_y]);
      z.domain(3);

      g.append("g")
          .attr("class", "axis axis--x")
          .attr("transform", "translate(0," + height + ")")
          .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%d-%m-%y")))
          .selectAll("text")
            .style("text-anchor", "end")
            .attr("dx", "-.8em")
            .attr("dy", ".15em")
            .attr("transform", "rotate(-60)" );

      g.append("g")
          .attr("class", "axis axis--y")
          .call(d3.axisLeft(y))
        .append("text")
          .attr("fill", "#000")
          .attr("transform", "rotate(-90)")
          .attr("y", 6)
          .attr("dy", "0.71em")
          .style("text-anchor", "end")
          //.text("Operações");


      g.selectAll(".serie")
        .data(stack.keys(["vm","ap","ep"])(rec))
        .enter().append("g")
          .attr("class", "serie")
            .attr("fill", function(d) { return z(d.key); })
        .selectAll("rect")
        .data(function(d) { return d; })
        .enter().append("rect")
          .attr("x",  function(d) {return x(d.data.date) - (width/rec.length/2) ; })
          .attr("y", function(d) { return y(d[1]); })
          .attr("height",0)
          //.attr("width", x.bandwidth());
          .attr("width", width/rec.length*0.95)
          .transition().duration(2000)
          .attr("height", function(d) { return y(d[0]) - y(d[1]); });

    g.append("text")
            .attr("id", "center_text2")
            .style("fill", "black")
            .style("font-size", "14px")
            .attr("dy", ".25em")
            .attr("text-anchor", "left")
            .attr("y", -20)
            .attr("x", 40)
            .text("Operações por tipo nos últimos " + rec.length + " dias");
  }


function wktapp_objects_tree(Data){
    var margin = {top: 10, right: 25, bottom: 10, left: 100},
        width = 960 - margin.left - margin.right,
        height = 700 - margin.top - margin.bottom;

    var  treeData = JSON.parse(Data);


    var svg = d3.select("#wktapp_treeview")
        .append("svg")
        .attr("width", width + margin.right + margin.left)
        .attr("height", height + margin.top + margin.bottom)
      .append("g")
        .attr("transform", "translate("
              + margin.left + "," + margin.top + ")");

    var i = 0,
        duration = 750,
        root;

    // declares a tree layout and assigns the size
    var treemap = d3.tree().size([height, width]);

    // Assigns parent, children, height, depth
    root = d3.hierarchy(treeData, function(d) { return d.children; });
    root.x0 = height / 2;
    root.y0 = 0;

    // Collapse after the second level
    root.children.forEach(collapse);

    update(root);

    // Collapse the node and all it's children
    function collapse(d) {
      if(d.children) {
        d._children = d.children
        d._children.forEach(collapse)
        d.children = null
      }
    }

    function update(source) {

      // Assigns the x and y position for the nodes
      var treeData = treemap(root);

      // Compute the new tree layout.
      var nodes = treeData.descendants(),
          links = treeData.descendants().slice(1);

      // Normalize for fixed-depth.
      nodes.forEach(function(d){ d.y = d.depth * 180});

      // ****************** Nodes section ***************************

      // Update the nodes...
      var node = svg.selectAll('g.node')
          .data(nodes, function(d) {return d.id || (d.id = ++i); });

      // Enter any new modes at the parent's previous position.
      var nodeEnter = node.enter().append('g')
          .attr('class', 'node')
          .attr("transform", function(d) {
            return "translate(" + source.y0 + "," + source.x0 + ")";
        })
        .on('click', click);

      // Add Circle for the nodes
      nodeEnter.append('circle')
          .attr('class', 'node')
          .attr('r', 1e-6)
          .style("fill", function(d) {
              return d._children ? "lightsteelblue" : "#fff";
          });

      // Add labels for the nodes
      nodeEnter.append('text')
          .attr("dy", ".35em")
          .attr("x", function(d) {
              return d.children || d._children ? -13 : 13;
          })
          .attr("text-anchor", function(d) {
              return d.children || d._children ? "end" : "start";
          })
          .text(function(d) { return d.data.code; });

      // UPDATE
      var nodeUpdate = nodeEnter.merge(node);

      // Transition to the proper position for the node
      nodeUpdate.transition()
        .duration(duration)
        .attr("transform", function(d) {
            return "translate(" + d.y + "," + d.x + ")";
         });

      // Update the node attributes and style
      nodeUpdate.select('circle.node')
        .attr('r', function(d) {
            var rad_circle = 10;
            if (d.data.lev==0){rad_circle=0}
            else if (d.data.lev==-1){rad_circle=4}
            else if (d.data.lev==-2){rad_circle=1}
            return rad_circle;
        })
        .style("fill", function(d) {
            return d._children ? "gray" : "#fff";
        })
        .style("stroke", function(d) {
            var col = "#68467a";
            if (d.data.typeof=='map'){col="steelblue"}
            else if (d.data.typeof=='layout'){col="#5cb85c"}
            else if (d.data.typeof=='sub_layout'){col="#5cb85c"};
            return col;
        })
        .attr('cursor', 'pointer');


      // Remove any exiting nodes
      var nodeExit = node.exit().transition()
          .duration(duration)
          .attr("transform", function(d) {
              return "translate(" + source.y + "," + source.x + ")";
          })
          .remove();

      // On exit reduce the node circles size to 0
      nodeExit.select('circle')
        .attr('r', 1e-6);

      // On exit reduce the opacity of text labels
      nodeExit.select('text')
        .style('fill-opacity', 1e-6);

      // ****************** links section ***************************

      // Update the links...
      var link = svg.selectAll('path.link')
          .data(links, function(d) { return d.id; });

      // Enter any new links at the parent's previous position.
      var linkEnter = link.enter().insert('path', "g")
          .attr("class", "link")
          .attr('d', function(d){
            var o = {x: source.x0, y: source.y0}
            return diagonal(o, o)
          });

      // UPDATE
      var linkUpdate = linkEnter.merge(link);

      // Transition back to the parent element position
      linkUpdate.transition()
          .duration(duration)
          .attr('d', function(d){ return diagonal(d, d.parent) });

      // Remove any exiting links
      var linkExit = link.exit().transition()
          .duration(duration)
          .attr('d', function(d) {
            var o = {x: source.x, y: source.y}
            return diagonal(o, o)
          })
          .remove();

      // Store the old positions for transition.
      nodes.forEach(function(d){
        d.x0 = d.x;
        d.y0 = d.y;
      });

      // Creates a curved (diagonal) path from parent to the child nodes
      function diagonal(s, d) {

        path = `M ${s.y} ${s.x}
                C ${(s.y + d.y) / 2} ${s.x},
                  ${(s.y + d.y) / 2} ${d.x},
                  ${d.y} ${d.x}`

        return path
      }

      // Toggle children on click.
      function click(d) {
        if (d.children) {
            d._children = d.children;
            d.children = null;
          } else {
            d.children = d._children;
            d._children = null;
          }
        update(d);
      }
    }

 }