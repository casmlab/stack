/*Displays line graph
*/

function display_linegraph(xaxisvalues,yaxisvalues,prmtext,elementid){

$(function () {
    var chart = Highcharts.chart(elementid, {

        title: {
            text: prmtext
        },

        subtitle: {
            text: ''
        },

        xAxis: {
            categories: xaxisvalues
        },


        series: [{
            type: 'column',
            colorByPoint: true,
            data: yaxisvalues,
            showInLegend: false
	        
}]

    });



});
}





var modal = document.getElementById('myModal');
// Get the <span> element that closes the modal

// When the user clicks on <span> (x), close the modal
function closemodel() {
document.getElementById("loader").style.display="none";
    modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}


