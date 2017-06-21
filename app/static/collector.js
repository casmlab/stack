function displayTweets(res, tabnumber) {
    var information = "<br>";
    var usertweetinfo = "<br><b>----Tweets by---------" + document.getElementById("header").innerHTML + "----</b><br>";
 
    var tweets = res.tweets.split("||");
    var users = res.users.split("||");
    var createddate=res.createdtime.split("||");
for (var i = 1; i < tweets.length; i++) {
    if (tabnumber == 1) {
        
            information = information + "<b>" + users[i] + " :</b>" + tweets[i].trim() ;
        }
     else {
        
            information = information + tweets[i].trim() ;
        }
information=information+"  <b> Posted On:"+createddate[i]+"</b><br>"
    }

    if (tweets.length == 1) {
        setPageandDateDefault();
        information = "Information Not Present";
        //pagenum=0;

    }
  
    if (tweets.length <= 20) {
        setPageandDateDefault()

    } else
        localStorage.setItem("createdts", res.createdts);
    document.getElementById("putdata").innerHTML = information;

    /* if (tweets.length <= 20)
                    pagenum = 0;
              //  localStorage.setItem("setpagenumber", pagenum);
*/
}



function displayTermValues(res) {

    information = "<b>Name:</b>" + res.names +
        "<br> <b> Description: </b> " + res.description + "<br>" +
        "<b>Friend Count: </b> " + res.friends_count +
        "<br><b>Location: </b>" + res.location +
        "<br><b>Favourite Count: </b>" + res.favouritecount +
        "<br><b>Status Count: </b>" + res.statuscount +
        "<br><b>Followers: </b>" + res.followers + "<br><b>----OUR DATABASE STATS---</b><br>" + 
		"<br><b>Tweets By " + res.names + ":</b> " + res.total_tweets+
		"<br><b>Total URLS: </b>" + res.totalurls +		
        "<br><b>Total Tweets with Hashtags: </b>" + res.hashtagscounter +
        "<br><b>Total Tweets with exclamation: </b> " + res.tweets_with_exclaim +
        "<br><b>Total Tweets with User mentions: </b> " + res.tweets_user_mentions;
    document.getElementById("header").style.color = "#" + res.headercolor;
    document.getElementById("header").innerHTML = res.names

    document.getElementById("modalheader").style.backgroundColor = "#5cb85c";

    /*sets time to fetch tweets ,all tweets must be after epoch time*/
    setPageandDateDefault();
    document.getElementById("putdata").innerHTML = information;


}


function dataretriveFailed(reason) {
    document.getElementById("modalheader").style.backgroundColor = "#EE0000";
    document.getElementById("putdata").innerHTML = reason;
    document.getElementById("header").innerHTML = "";
    document.getElementById("tabs").style.display = "none";
    document.getElementById("tweetsdisplay").style.display = "none";
}


function setPageandDateDefault() {
    try {
        var currentdate = new Date();
        var currdate = currentdate.getFullYear() + "-" +
            (currentdate.getMonth() + 1) + "-" +
            (currentdate.getDate()) +
            "T" + currentdate.getHours() + ":" +
            currentdate.getMinutes() + ":" + currentdate.getSeconds() + "Z";

        localStorage.setItem("createdts", currdate);
        //  localStorage.setItem("createdts", "1970-01-01T00:00:00Z");
       // localStorage.setItem("setpagenumber", "0");
    } catch (e) {console.log(e)}
}

function showLoader() {
    document.getElementById("loader").style.display = "block";
}

function hideLoader() {
    document.getElementById("loader").style.display = "none";
}



function switchTab(tabnumber) {
    setPageandDateDefault();
    tabstatus = tabnumber;
    if (tabnumber == 1) {
        $("#termstats").removeClass("active");
        $("#tweetsby").removeClass("active");
        $("#tweetsto").addClass("active");
        document.getElementById("tweetsdisplay").style.display = "block";
        showtweets(1, tabnumber)
    } else if (tabnumber == 3) {
        ShowContent(localStorage.getItem("termid"));
        $("#tweetsby").removeClass("active");
        $("#tweetsto").removeClass("active");
        $("#termstats").addClass("active");
        //tabstatus=1;
    } else {
        $("#tweetsto").removeClass("active");
        $("#termstats").removeClass("active");
        $("#tweetsby").addClass("active");
        document.getElementById("tweetsdisplay").style.display = "block";
        showtweets(1, tabnumber)
    }



}

function setJsonmap(termid) {

    if (termid != localStorage.getItem("termid")) {
        tweet_object = {};


    }


}

function GetData(tweet_object, tabstatus, range, limit) {
    var jsonobj = new Object();
    jsonobj.tweets = tweet_object[tabstatus + "tweets"][range];
    jsonobj.users = tweet_object[tabstatus + "users"][range];
    jsonobj.limit = tweet_object[tabstatus + "limit"]
    jsonobj.createdtime = tweet_object[tabstatus + "created_ts"][range];
 
    return jsonobj;
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

function showhide_extralinks(limit, upperlimit = 10) {
    try {
	
    
            //diff = diff - limit;
            for (var i = 1; i <= upperlimit; i++) {
				$("#st"+i).removeClass("active")
                document.getElementById("st" + i).style.display = "none";
            }


        
            for (var i = 1; i <=limit ;i++) {
               
                document.getElementById("st" + i).style.display = "block";
            
        }
    } catch (e) {
        console.log(e);
    }
}



function move_next() {

    var number = (document.getElementsByClassName("active"))[1].innerHTML
    if (number <= 9) {
        showtweets(parseInt(number) + 1);

    }



}

function move_previous() {
    var number = (document.getElementsByClassName("active"))[1].innerHTML
    if (number >= 2) {
        showtweets(parseInt(number) - 1);

    }

}
