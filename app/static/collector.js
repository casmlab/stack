
function displayTweets(res,tabnumber)
{
  var information = "<br>";
                var usertweetinfo = "<br><b>----Tweets by---------" + document.getElementById("header").innerHTML + "----</b><br>";
                    var pagenum = parseInt(localStorage.getItem("setpagenumber"));
                    pagenum = pagenum + 1;
                    var tweets = res.tweets.split("||");
                    var users = res.users.split("||");
                    if (tabnumber == 1) {
                        for (var i = 1; i < tweets.length; i++) {
                            information = information + "<b>" + users[i] + " :</b>" + tweets[i] + "<br>";
                        }
                    } else {
                        for (var i = 1; i < tweets.length; i++) {
                            information = information + tweets[i] + "<br>";
                        }

                    }

                 if (tweets.length ==1) {
                 setPageandDateDefault();
				information="Information Not Present";
				pagenum=0;
				
                }
                //alert(res.createdts);
                if (tweets.length <= 20) {
                 setPageandDateDefault()

                } else
                    localStorage.setItem("createdts", res.createdts);
                document.getElementById("putdata").innerHTML = information;
                document.getElementById("pagenum").innerHTML = "<b>Page: " + pagenum + "</b>";
//alert(res.createdts);
                if (tweets.length <= 20)
                    pagenum = 0;
                localStorage.setItem("setpagenumber", pagenum);
}



function displayTermValues(res)
{

information = "<b>Name:</b>" + res.names +
                            "<br> <b> Description </b>: " + res.description + "<br>" +
                            "<b>Friend Count</b>: " + res.friends_count +
                            "<br><b>Location:</b>" + res.location +
                            "<br><b>Favourite Count:</b>" + res.favouritecount +
                            "<br><b>Status Count:</b>" + res.statuscount +
                            "<br><b>Followers:</b>" + res.followers + "<br><b>Total URLS:</b>" + res.totalurls +
                            "<br><b>Total Tweets with Hashtags:</b>" + res.hashtagscounter +
                            "<br><b>Total Tweets with exclamation :</b>" + res.tweets_with_exclaim +
                            "<br><b>Total Tweets with User mentions :</b>" + res.tweets_user_mentions +
                            "<br><b>Total Tweets with Re-tweeted :</b>" + res.total_retweets;
                        document.getElementById("header").style.color = "#" + res.headercolor;
                        document.getElementById("header").innerHTML = res.names+
						  "<br><b>Tweets By "+res.names+" :</b>" + res.total_tweets;
                        document.getElementById("modalheader").style.backgroundColor = "#5cb85c";
                    
                    /*sets time to fetch tweets ,all tweets must be after epoch time*/
                    setPageandDateDefault();
                    document.getElementById("putdata").innerHTML = information;
                

}


function dataretriveFailed(reason)
{
 document.getElementById("modalheader").style.backgroundColor = "#EE0000";
document.getElementById("putdata").innerHTML =reason;
document.getElementById("header").innerHTML = "";
}


function setPageandDateDefault() {
try{
    var currentdate=new Date();
    var currdate=currentdate.getFullYear()+"-"+
currentdate.getDate()+"-"+
	     (currentdate.getMonth()+1)+
		"T"+currentdate.getHours()+":"+
		currentdate.getMinutes()+":"+currentdate.getSeconds()+"Z";
		
localStorage.setItem("createdts",currdate);
  //  localStorage.setItem("createdts", "1970-01-01T00:00:00Z");
    localStorage.setItem("setpagenumber", "0");
}
catch(e){}
}

function showLoader()
{
document.getElementById("loader").style.display = "block";
}

function hideLoader()
{document.getElementById("loader").style.display = "none";}



function switchTab(tabnumber) {
    setPageandDateDefault();
    tabstatus=tabnumber;
if(tabnumber==1)
{
$("#termstats").removeClass("active");
$("#tweetsby").removeClass("active");
$("#tweetsto").addClass("active");
    showtweets(tabnumber)
}
else if(tabnumber==3)
{
ShowContent(document.getElementById("tweetsdisplay").value);
$("#tweetsto").removeClass("active");
$("#tweetsby").removeClass("active");
$("#termstats").addClass("active");
	
	tabstatus=1;
}	

else{
$("#tweetsto").removeClass("active");
$("#termstats").removeClass("active");
$("#tweetsby").addClass("active");
    showtweets(tabnumber)
	}
	
	

}


function search() {
    flag = 1;
    searchterm = document.getElementById("searchterm").value;
    for (i = 0; i < terms.length; i++) {
        terms[i].parentElement.style.display = "";
        if (!terms[i].innerHTML.includes(searchterm)) {
            terms[i].parentElement.style.display = "none";
        } else {
            flag = 0;
        }

    }
    if (flag == 1) {
        document.getElementById("notermmsg").style.display = "block";
    } else
        document.getElementById("notermmsg").style.display = "none";
}







