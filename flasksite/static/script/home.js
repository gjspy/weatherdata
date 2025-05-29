(function() {
	const FCST_TIME_BUFFER_DAYS = 2;


	function pane1(yesterdayMO, yesterdayBC, gradeByLocArr, bestOrg) {
		let moTablesCont = document.querySelector("#homepage .pane-1 .entry.mo .table-cont");
		api.dom.FillSummaryTableGrades(moTablesCont, yesterdayMO.data);

		let bcTablesCont = document.querySelector("#homepage .pane-1 .entry.bbc .table-cont");
		api.dom.FillSummaryTableGrades(bcTablesCont, yesterdayBC.data);


		let moGradeDOM = document.querySelector("#homepage .pane-1 .entry.mo > a.grade");
		api.dom.setElemGrade(moGradeDOM, yesterdayMO.ga);

		let bcGradeDOM = document.querySelector("#homepage .pane-1 .entry.bbc > a.grade");
		api.dom.setElemGrade(bcGradeDOM, yesterdayBC.ga);

		console.log(gradeByLocArr);
		let colours = api.dom.getMapColours(gradeByLocArr, "hyp");
		api.dom.initMap({
			selector: ".pane-1 #hero-map",
			popup: false,
			colours: colours
		});

		let title = document.querySelector("#homepage .pane-1 .footer > .main");
		
		if (bestOrg === "MO") {
			title.textContent = title.textContent.replace("[org]", "The Met Office was");
		} else if (bestOrg === "BBC") {
			title.textContent = title.textContent.replace("[org]", "BBC Weather was");
		} else {
			title.textContent = "Both organisations had the same accuracy"
		};
	};

	function pane2ChangeLoc(data, pinColour) {
		let locTitle = document.querySelector("#homepage .pane-2 .title-bar .right-items .main");

		api.dom.setElemGrade(locTitle, pinColour);
		locTitle.textContent = api.siteInfoDict[data.loc].clean_name;

		let moTable = document.querySelector("#homepage .pane-2 #mo-summary table");
		api.dom.FillSummaryTableConditions(moTable, data.mo);

		let bbcTable = document.querySelector("#homepage .pane-2 #bbc-summary table");
		api.dom.FillSummaryTableConditions(bbcTable, data.bbc);

		api.dom.setElemGrade(document.querySelector("#homepage .pane-2 #mo-summary > label.grade"), (data.mo || {}).ga);
		api.dom.setElemGrade(document.querySelector("#homepage .pane-2 #bbc-summary > label.grade"), (data.bbc || {}).ga);
	};


	function pane2(gradeByLocArr) {
		let colours = api.dom.getMapColours(gradeByLocArr, "hyp");

		api.dom.initMap({
			selector: ".pane-2 #hero-map",
			popup: false,
			colours: colours,
			onPinSelect: pane2ChangeLoc,
			data: gradeByLocArr
		});
	};


	function pane3(weekDataForCalendar, veryBest) {
		function dateOnHover(dateElem, period, dt, calendarCont, bestOrg, bestGrade) {
			let moData = api.calc.getOrgFromPeriod(period, "MO").data;
			let bcData = api.calc.getOrgFromPeriod(period, "BBC").data;

			//let dateMOGrades = period.data.map((v) => v.moGrade);
			//let dateBBCGrades = period.data.map((v) => v.bbcGrade);
		
			let moTablesCont = document.querySelector("#homepage .pane-3 .detail #mo-summary");
			api.dom.FillSummaryTableGrades(moTablesCont, moData);//dateMOGrades);
		
			let bbcTablesCont = document.querySelector("#homepage .pane-3 .detail #bbc-summary");
			api.dom.FillSummaryTableGrades(bbcTablesCont, bcData);//dateBBCGrades);
		
			
			let moGradeDOM = document.querySelector("#homepage .pane-3 .detail #mo-summary > label[grade]");
			api.dom.setElemGrade(moGradeDOM, moData.ga);
		
			let bbcGradeDOM = document.querySelector("#homepage .pane-3 .detail #bbc-summary > label[grade]");
			api.dom.setElemGrade(bbcGradeDOM, bcData.ga);
		};


		let selector = "#homepage .pane-3 .calendar";
		api.dom.FillCalendar(
			selector,
			weekDataForCalendar,
			7,
			"dynamicWeeksWithGaps",
			dateOnHover
		)

		api.dom.insertSVGByOrg(document.querySelector("#homepage .pane-3 .title-bar svg"), veryBest);

		let detail = document.querySelector("#homepage .pane-3 .detail");
		document.querySelector(selector).append(detail);

		let title = document.querySelector("#homepage .pane-3 .title-bar > .main");

		if (veryBest === "MO") {
			title.textContent = title.textContent.replace("[org]", "The Met Office was");
		} else if (veryBest === "BBC") {
			title.textContent = title.textContent.replace("[org]", "BBC Weather was");
		} else {
			title.textContent = "Both organisations had the same accuracy"
		};
	};




	async function pane4() {
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


		let monthly = await api.api.getApiMonthOfDailySummaries(FCST_TIME_BUFFER_DAYS);

		let dataForCalendar = [];
		for (let [k,v] of Object.entries(monthly)) {
			v.ft = k;
			dataForCalendar.push(v);
		};

		let selector = "#homepage .pane-4 .calendar";

		api.dom.FillCalendar(
			selector,
			dataForCalendar,
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
			title.textContent = title.textContent.replace("[org]", "The Met Office was");
			subtitle.textContent = subtitle.textContent
				.replace("[org1]", "The Met Office")
				.replace("[time]", diffStr)
				.replace("[org2]", "BBC Weather");

		} else if ((counts.MO || 0) < (counts.BBC || 0)) {
			title.textContent = title.textContent.replace("[org]", "BBC Weather was");
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
		let weeklySummary = await api.api.getApiWeekOfDailySummaries(FCST_TIME_BUFFER_DAYS);
		let datas = Object.values(weeklySummary);

		let datesInWeek = Array.from(Object.keys(weeklySummary)).map( v => Date.parse(v) );
		let yesterday = datas[datesInWeek.indexOf(Math.max(...datesInWeek))];

		let yesterdayMO = api.calc.getOrgFromPeriod(yesterday, "MO")
		let yesterdayBC = api.calc.getOrgFromPeriod(yesterday, "BBC")

		let gradeByLocArr = api.calc.getGradeByLocArr(yesterdayMO.data, yesterdayBC.data);
		
		//let moScoreYday = api.calc.averageOfGrades(yesterdayMO.data.map( v => v.ga ), true);
		//let bcScoreYday = api.calc.averageOfGrades(yesterdayBC.data.map( v => v.ga ), true);

		let bestYesterday = api.calc.getBestOrgFromPeriods([yesterday]);
		let bestOverWeek = api.calc.getBestOrgFromPeriods(datas);

		let weekDataForCalendar = [];
		for (let [k,v] of Object.entries(weeklySummary)) {
			v.ft = k;
			weekDataForCalendar.push(v);
		};

		console.log("grade by loc arr", gradeByLocArr);
		
		pane1(yesterdayMO, yesterdayBC, gradeByLocArr, bestYesterday);
		pane2(gradeByLocArr);
		pane3(weekDataForCalendar, bestOverWeek);

		document.querySelector("#homepage").setAttribute("rendered", "true");

		pane4();
	};

	Main();
})()