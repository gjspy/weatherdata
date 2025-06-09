(function() {
	const FCST_TIME_BUFFER_DAYS = 1;//2;


	function pane1(yesterdayMO, yesterdayBC, gradeByLocArr, bestOrg) {
		let moGradeDOM = document.querySelector("#homepage .pane-1 .entry.mo > .header > a.grade");
		api.dom.setElemGrade(moGradeDOM, yesterdayMO.ga);

		let bcGradeDOM = document.querySelector("#homepage .pane-1 .entry.bbc > .header > a.grade");
		api.dom.setElemGrade(bcGradeDOM, yesterdayBC.ga);

		let mapGrades = api.dom.getMapGrades(gradeByLocArr, "hyp");

		try {
			api.dom.initMap({
				selector: ".pane-1 #hero-map",
				popup: false,
				grades: mapGrades
			});
		} catch(err) {
			console.error("couldn't init map", err);
		};		

		let subtitle = document.querySelector("#homepage .pane-1 .footer .sub");
		subtitle.textContent = subtitle.textContent.replaceAll("[PIE_CHART_GRADE_DESC]", api.descriptions.PIE_CHART_GRADES);
	};

	function pane2ChangeLoc(data, pinElem) {
		let locTitle = document.querySelector("#homepage .pane-2 .title-bar .right-items .main");

		let grade = (pinElem) ? pinElem.getAttribute("grade") : "F";

		api.dom.setElemGrade(locTitle, grade);
		locTitle.textContent = api.siteInfoDict[data.loc].clean_name;

		let moTable = document.querySelector("#homepage .pane-2 #mo-summary table");
		api.dom.FillSummaryTableConditions(moTable, data.mo);

		let bbcTable = document.querySelector("#homepage .pane-2 #bbc-summary table");
		api.dom.FillSummaryTableConditions(bbcTable, data.bbc);

		api.dom.setElemGrade(document.querySelector("#homepage .pane-2 #mo-summary .left-items label.grade"), (data.mo || {}).ga);
		api.dom.setElemGrade(document.querySelector("#homepage .pane-2 #bbc-summary .left-items label.grade"), (data.bbc || {}).ga);
	};


	function pane2(gradeByLocArr) {
		let grades = api.dom.getMapGrades(gradeByLocArr, "hyp");

		let subtitle = document.querySelector("#homepage .pane-2 .title-bar .sub");
		subtitle.textContent = subtitle.textContent
			.replaceAll("[FCST_BUFFER_HOURS]", String(FCST_TIME_BUFFER_DAYS * 24))
			.replaceAll("[SUMMARY_DESC]", api.descriptions.SUMMARY);

		pane2ChangeLoc(gradeByLocArr[0], undefined);

		try {
			api.dom.initMap({
				selector: ".pane-2 #hero-map",
				popup: false,
				grades: grades,
				onPinSelect: pane2ChangeLoc,
				data: gradeByLocArr
			});
		} catch(err) {
			console.error("couldn't init map", err);
		};		
	};

	function pane3DateOnHover(dateElem, period, dt, calendarCont, bestOrg, bestGrade, isClick) {
		for (let e of calendarCont.querySelectorAll(".clicked")) e.classList.remove("clicked");

		if (isClick) dateElem.classList.add("clicked");
		

		let moData = api.calc.getOrgFromPeriod(period, "MO");
		let bcData = api.calc.getOrgFromPeriod(period, "BBC");
	
		//let moTablesCont = document.querySelector();
		//api.dom.FillSummaryTableGrades(moTablesCont, moData.data);//dateMOGrades);
		api.dom.FillSummaryPieGrades("#homepage .pane-3 .detail #mo-summary .pie-cont", moData.data, true);
	
		//let bbcTablesCont = document.querySelector("#homepage .pane-3 .detail #bbc-summary");
		//api.dom.FillSummaryTableGrades(bbcTablesCont, bcData.data);//dateBBCGrades);
		api.dom.FillSummaryPieGrades("#homepage .pane-3 .detail #bbc-summary .pie-cont", bcData.data, true);		
		
		let moGradeDOM = document.querySelector("#homepage .pane-3 .detail #mo-summary .left-items label[grade]");
		api.dom.setElemGrade(moGradeDOM, moData.ga);
	
		let bbcGradeDOM = document.querySelector("#homepage .pane-3 .detail #bbc-summary .left-items label[grade]");
		api.dom.setElemGrade(bbcGradeDOM, bcData.ga);
	};


	function pane3(weekDataForCalendar, veryBest) {
		// need identifier, so we don't worry about hrs/min/sec ****
		let today = new Date();
		let yesterdayId = api.datetime.indentifierFromDate(new Date(today.getTime() - (1000 * 60 * 60 * 24))); 

		let selector = "#homepage .pane-3 .calendar";
		api.dom.FillCalendar(
			selector,
			weekDataForCalendar,
			7,
			"dynamicWeeksWithGaps",
			pane3DateOnHover,
			{ [yesterdayId]: "- <i>Yesterday</i>" }
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

		let subtitle = document.querySelector("#homepage .pane-3 .title-bar .sub:last-of-type");
		subtitle.textContent = subtitle.textContent.replaceAll("[FCST_BUFFER_HOURS]", String(FCST_TIME_BUFFER_DAYS * 24));

		let pieDesc = document.querySelector("#homepage .pane-3 .calendar .detail .info");
		pieDesc.textContent = pieDesc.textContent.replaceAll("[PIE_CHART_GRADE_DESC]", api.descriptions.PIE_CHART_GRADES);
	};




	async function pane4() {
		function dateOnHover(dateElem, period, dt, calendarCont, bestOrg, bestGrade, isClick) {
			if (bestOrg === "EQUALS") return;

			//for (let e of calendarCont.querySelectorAll(".clicked")) e.classList.remove("clicked");
			//if (isClick) dateElem.classList.add("clicked");

			let calendar = calendarCont.offsetParent;

			let current = calendar.querySelector(".date[floating]");
			if (current) {
				if (current.__floatingOn === dateElem) return;

				current.remove();
			};

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
			floatElem.__floatingOn = dateElem;

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

		let todayId = api.datetime.indentifierFromDate(new Date());

		api.dom.FillCalendar(
			selector,
			dataForCalendar,
			api.config.monthNDays,
			"regularWeeks",
			dateOnHover,
			{ [todayId]: "- <i>Today</i>" }
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
		let diffStr = (diff === 1) ? "1 more outperforming day" : String(diff) + " more outperforming days";

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
			subtitle.textContent = `Each had ${timeStr} where they outperformed the other.`;
		};

		
		
	};

	function onGoogleChartsLoad(yesterdayMO, yesterdayBC, weekDataForCalendar, bestOverWeek) {
		api.dom.FillSummaryPieGrades("#homepage .pane-1 .entry.mo .pie-cont", yesterdayMO.data);
		api.dom.FillSummaryPieGrades("#homepage .pane-1 .entry.bbc .pie-cont", yesterdayBC.data);
		
		let pane3Clicked = document.querySelector("#homepage .pane-3 .clicked");
		if (!pane3Clicked) pane3Clicked = document.querySelector("#homepage .pane-3 .date:last-of-type");

		pane3DateOnHover(pane3Clicked, weekDataForCalendar[weekDataForCalendar.length - 1], undefined, pane3Clicked.parentElement, undefined, undefined, true);
	};



	async function Main() {
		let weeklySummary = await api.api.getApiWeekOfDailySummaries(FCST_TIME_BUFFER_DAYS);
		let datas = Object.values(weeklySummary);

		let datesInWeek = Array.from(Object.keys(weeklySummary)).map( v => Date.parse(v) );
		let yesterday = datas[datesInWeek.indexOf(Math.max(...datesInWeek))];

		let yesterdayMO = api.calc.getOrgFromPeriod(yesterday, "MO");
		let yesterdayBC = api.calc.getOrgFromPeriod(yesterday, "BBC");

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

		pane1(yesterdayMO, yesterdayBC, gradeByLocArr, bestYesterday);
		pane2(gradeByLocArr);
		pane3(weekDataForCalendar, bestOverWeek);

		google.charts.load("current", {"packages": ["corechart"]});
		google.charts.setOnLoadCallback(() => onGoogleChartsLoad(yesterdayMO, yesterdayBC, weekDataForCalendar, bestOverWeek));
		window.onresize = () => onGoogleChartsLoad(yesterdayMO, yesterdayBC, weekDataForCalendar, bestOverWeek);

		document.querySelector("#homepage").setAttribute("rendered", "true");

		pane4();
	};

	Main();
})()