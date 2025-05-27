function onInnerScroll(contentCont) {
	document.body.style.setProperty("--scroll-height", `${contentCont.scrollTop}px`);

	document.body.style.getComputed
};

function rand(min, max, places) {
	let seed = Math.random();
	return min + (Math.floor((max - min) * (10**places) * seed) / (10**places));
};

console.log("HOME", document.readyState);


//initMap("", false, "loc");

//document.querySelector("#loc-card").addEventListener("click", function() {
//	initMap("#popup-map-cont", true);
//});

//let content = document.querySelector("#content");

//content.onscroll = () => {
//	onInnerScroll(content);
//};
//onInnerScroll(content);




function pane1(weeklyData, veryBest) {
	let yesterdayMOGrades = weeklyData[0].data.map((v) => v.moGrade);
	let yesterdayBBCGrades = weeklyData[0].data.map((v) => v.bbcGrade);

	let moTablesCont = document.querySelector("#homepage .pane-1 .entry.mo .table-cont");
	api.dom.FillSummaryTableGrades(moTablesCont, yesterdayMOGrades);

	let bbcTablesCont = document.querySelector("#homepage .pane-1 .entry.bbc .table-cont");
	api.dom.FillSummaryTableGrades(bbcTablesCont, yesterdayBBCGrades);


	let moGradeDOM = document.querySelector("#homepage .pane-1 .entry.mo > a.grade");
	api.dom.setElemGrade(moGradeDOM, weeklyData[0].nationwideMO);

	let bbcGradeDOM = document.querySelector("#homepage .pane-1 .entry.bbc > a.grade");
	api.dom.setElemGrade(bbcGradeDOM, weeklyData[0].nationwideBBC);

	let colours = api.dom.getMapColours(weeklyData[0].data, "hyp");
	api.dom.initMap({
		selector: ".pane-1 #hero-map",
		popup: false,
		colours: colours
	});

	let title = document.querySelector("#homepage .pane-1 .footer > .main");
	
	if (veryBest === "MO") {
		title.textContent = title.textContent.replace("[org]", "The Met Office were");
	} else if (veryBest === "BBC") {
		title.textContent = title.textContent.replace("[org]", "BBC Weather were");
	} else {
		title.textContent = "Both organisations had the same accuracy"
	};
};

function pane2ChangeLoc(data) {
	let locTitle = document.querySelector("#homepage .pane-2 .title-bar .right-items .main");

	api.dom.setElemGrade(locTitle, data.hypAvg);
	locTitle.textContent = api.siteInfoDict[data.loc].clean_name;

	let moTable = document.querySelector("#homepage .pane-2 #mo-summary table");
	api.dom.FillSummaryTableConditions(moTable, data.mo);

	let bbcTable = document.querySelector("#homepage .pane-2 #bbc-summary table");
	api.dom.FillSummaryTableConditions(bbcTable, data.bbc);

	api.dom.setElemGrade(document.querySelector("#homepage .pane-2 #mo-summary > label.grade"), data.moGrade);
	api.dom.setElemGrade(document.querySelector("#homepage .pane-2 #bbc-summary > label.grade"), data.bbcGrade);
};


function pane2(weeklyData) {
	let colours = api.dom.getMapColours(weeklyData[0].data, "hyp");

	api.dom.initMap({
		selector: ".pane-2 #hero-map",
		popup: false,
		colours: colours,
		onPinSelect: pane2ChangeLoc,
		data: weeklyData[0].data
	});
};


function pane3(weeklyData, veryBest) {
	function dateOnHover(dateElem, period, dt, calendarCont, bestOrg, bestGrade) {
		let dateMOGrades = period.data.map((v) => v.moGrade);
		let dateBBCGrades = period.data.map((v) => v.bbcGrade);
	
		let moTablesCont = document.querySelector("#homepage .pane-3 .detail #mo-summary");
		api.dom.FillSummaryTableGrades(moTablesCont, dateMOGrades);
	
		let bbcTablesCont = document.querySelector("#homepage .pane-3 .detail #bbc-summary");
		api.dom.FillSummaryTableGrades(bbcTablesCont, dateBBCGrades);
	
		
		let moGradeDOM = document.querySelector("#homepage .pane-3 .detail #mo-summary > label[grade]");
		api.dom.setElemGrade(moGradeDOM, period.nationwideMO);
	
		let bbcGradeDOM = document.querySelector("#homepage .pane-3 .detail #bbc-summary > label[grade]");
		api.dom.setElemGrade(bbcGradeDOM, period.nationwideBBC);
	};


	let selector = "#homepage .pane-3 .calendar";
	api.dom.FillCalendar(
		selector,
		weeklyData,
		7,
		"dynamicWeeksWithGaps",
		dateOnHover
	)

	api.dom.insertSVGByOrg(document.querySelector("#homepage .pane-3 .title-bar svg"), veryBest);

	let detail = document.querySelector("#homepage .pane-3 .detail");
	document.querySelector(selector).append(detail);

	let title = document.querySelector("#homepage .pane-3 .title-bar > .main");

	if (veryBest === "MO") {
		title.textContent = title.textContent.replace("[org]", "The Met Office were");
	} else if (veryBest === "BBC") {
		title.textContent = title.textContent.replace("[org]", "BBC Weather were");
	} else {
		title.textContent = "Both organisations had the same accuracy"
	};
};




function EvalPeriods(summary) {
	let moWeekOfNationwide = [];
	let bbcWeekOfNationwide = [];

	// MIGHT NOT BE NEEDED, API SHOULD PROVIDE THESE WHEN CALCULATED.
	let datei = 0;
	for (let date of summary) {
		let nationwideMO = [];
		let nationwideBBC = [];

		let i = 0;
		for (let entry of date.data) {
			let moGrades = Object.values(entry.mo).map((v) => v.grade);
			let bbcGrades = Object.values(entry.bbc).map((v) => v.grade);

			let moGrade = api.calc.averageOfGrades(moGrades); // i dont like this. i hope each time period is given an voerall score in calculations behind api.
			let bbcGrade = api.calc.averageOfGrades(bbcGrades);

			nationwideMO.push(moGrade);
			nationwideBBC.push(bbcGrade);

			summary[datei].data[i].moGrade = moGrade;
			summary[datei].data[i].bbcGrade = bbcGrade;

			summary[datei].data[i].hypAvg = api.calc.hyperbolicAvgGrades([moGrade, bbcGrade]);

			i ++;
		};

		date.nationwideMO = api.calc.averageOfGrades(nationwideMO);
		date.nationwideBBC = api.calc.averageOfGrades(nationwideBBC);

		moWeekOfNationwide.push(date.nationwideMO);
		bbcWeekOfNationwide.push(date.nationwideBBC);

		datei ++;
	};

	let moWeekScore = api.calc.averageOfGrades(moWeekOfNationwide, true);
	let bbcWeekScore = api.calc.averageOfGrades(bbcWeekOfNationwide, true);
	let veryBest;

	if (moWeekScore > bbcWeekScore) {
		veryBest = "MO";
	} else if (moWeekScore < bbcWeekScore) {
		veryBest = "BBC";
	} else {
		veryBest = "EQUALS";
	};

	return [summary, veryBest];
};



async function pane4(veryBest) {
	function dateOnHover(dateElem, period, dt, calendarCont, bestOrg, bestGrade) {
		if (bestOrg === "EQUALS") return;

		let calendar = calendarCont.offsetParent;

		if (calendar.querySelector(".date[floating=\"true\"]")) return;

		let floatElem = api.assets.dateOneGradeTemplate.cloneNode(true);
		api.dom.fillOneGradeDateElem(floatElem, period, dt, calendarCont, true);

		floatElem.querySelector(".datetxt").remove();

		// boundingRect() returns global space, need to calculate relative
		let calBounds = calendar.getBoundingClientRect(); 
		let bounds = dateElem.getBoundingClientRect();

		floatElem.style.position = "absolute";
		floatElem.style.top = String((bounds.top - calBounds.top - 2) + bounds.height) + "px";
		floatElem.style.left = String(bounds.left - calBounds.left - 1) + "px";
		floatElem.style["z-index"] = "101";
		

		floatElem.setAttribute("floating", "true");

		calendarCont.append(floatElem);

		setTimeout(() => {
			floatElem.style.opacity = "1";
		});
		
		dateElem.addEventListener("mouseleave", () => {
			floatElem.setAttribute("floating", "false");
			floatElem.style.opacity = "0";

			setTimeout(() => {
				floatElem.remove();
			}, 300);
		});
	};


	let monthly = await api.api.getApiMonthOfDailySummaries();
	[monthly, veryBest] = EvalPeriods(monthly);

	let selector = "#homepage .pane-4 .calendar";

	api.dom.FillCalendar(
		selector,
		monthly,
		api.config.monthNDays,
		"regularWeeks",
		dateOnHover
	)

	let elems = document.querySelectorAll(selector + " .calendar-cont > *");
	let counts = {};

	for (let elem of elems) {
		let v = elem.getAttribute("best");
		if (!v || v === "EQUALS") continue;

		if (!counts[v]) counts[v] = 0
		counts[v] ++;
	};

	//let countVals = Object.values(counts);
	//let best = Object.keys(counts)[countVals.indexOf(Math.max(...countVals))];

	let title = document.querySelector("#homepage .pane-4 .title-bar > .main");
	let subtitle = document.querySelector("#homepage .pane-4 .title-bar > .sub.detail");

	let diff = Math.abs((counts.MO || 0) - (counts.BBC || 0));
	let diffStr = (diff === 1) ? "1 more day" : String(diff) + " more days";

	if ((counts.MO || 0) > (counts.BBC || 0)) {
		title.textContent = title.textContent.replace("[org]", "The Met Office were");
		subtitle.textContent = subtitle.textContent
			.replace("[org1]", "The Met Office")
			.replace("[time]", diffStr)
			.replace("[org2]", "BBC Weather");

	} else if ((counts.MO || 0) < (counts.BBC || 0)) {
		title.textContent = title.textContent.replace("[org]", "BBC Weather were");
		subtitle.textContent = subtitle.textContent
			.replace("[org1]", "BBC Weather")
			.replace("[time]", diffStr)
			.replace("[org2]", "the Met Office");

	} else {
		let timeStr = ((counts.MO || 0) === 1) ? "1 day" : String((counts.MO || 0)) + " days";

		title.textContent = "Both organisations had the same accuracy";
		subtitle.textContent = `Each had ${timeStr} where they had greater accuracy than the other.`;
	};

	
	
};



async function Main() {
	let weeklySummary = await api.api.getApiWeekOfDailySummaries();
	[weeklySummary, veryBest] = EvalPeriods(weeklySummary);

	pane1(weeklySummary, veryBest);
	pane2(weeklySummary);
	pane3(weeklySummary, veryBest);
	pane4(weeklySummary, veryBest);
	document.querySelector("#homepage").setAttribute("rendered", "true");
};

Main();