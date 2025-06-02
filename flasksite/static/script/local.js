(function() {
	const FCST_TIME_BUFFER_DAYS = 2;

	async function pane1(locId) {
		let data = await api.api.getApiWeekOfDailySummaries(FCST_TIME_BUFFER_DAYS, locId);
		let datas = Object.values(data);

		let datesInWeek = Array.from(Object.keys(data)).map( v => Date.parse(v) );
		console.log(datesInWeek);
		let yesterday = datas[datesInWeek.indexOf(Math.max(...datesInWeek))];

		let yesterdayMO = api.calc.getOrgFromPeriod(yesterday, "MO");
		let yesterdayBC = api.calc.getOrgFromPeriod(yesterday, "BBC");


		let moTable = document.querySelector("#local .pane-1 #mo-summary table");
		api.dom.FillSummaryTableConditions(moTable, yesterdayMO.data[0]);

		let bbcTable = document.querySelector("#local .pane-1 #bbc-summary table");
		api.dom.FillSummaryTableConditions(bbcTable, yesterdayBC.data[0]);

		api.dom.setElemGrade(document.querySelector("#local .pane-1 #mo-summary > label.grade"), yesterdayMO.ga);
		api.dom.setElemGrade(document.querySelector("#local .pane-1 #bbc-summary > label.grade"), yesterdayBC.ga);
	};



	function fillHalfFcstObsPeriod(data, elem) {
		let wtElem = elem.querySelector(".wt");
		let tempElem = elem.querySelector(".temp");
		let windElem = elem.querySelector(".wind");
		let rainElem = elem.querySelector(".rain");

		if (data.w) {
			wtElem.setAttribute("src", `/static/icon/100/${data.w}.png`);

		}// else {
		//	wtElem.style.opacity = "0";
		//};

		if (data.t) tempElem.textContent = `${data.t}${api.units.temp}`;
		else if (data.tm && data.tx) tempElem.textContent = `${data.tm} - ${data.tx}${api.units.temp}`;
		//else tempElem.style.display = "none";

		if (data.ws) windElem.textContent = `${data.ws}${api.units.speed}`;
		//else windElem.style.display = "none";

		if (data.pp) rainElem.textContent = `${data.pp}${api.units.score}`;
		else if (data.pr) rainElem.textContent = `${data.pr}${api.units.precip}`;
		//else rainElem.style.display = "none";

	};

	function fillFullFcstObsPeriod(ft, data, elem) {
		let ftime = new Date(ft);

		let hr = ftime.getUTCHours();

		let timeText = elem.querySelector(".time");

		if (hr === 12) timeText.textContent = "12PM";
		else if (hr === 0) timeText.textContent = "12AM";
		else if (hr < 12) timeText.textContent = `${hr}AM`;
		else timeText.textContent = `${hr - 12}PM`;

		if (data.fcst) fillHalfFcstObsPeriod(data.fcst, elem.querySelector(".fcst"));
		if (data.obs) fillHalfFcstObsPeriod(data.obs, elem.querySelector(".obs"));

	};


	function fcstVsObsUpdate(data, contents, periods, selectedOrg, selectedSubOrg, selectedFcstTime) {
		if (!selectedOrg) {
			let chosen = api.random.choice(Object.keys(data.fcst));
			selectedOrg = chosen[0];
			selectedSubOrg = chosen[1];
		};

		// SET METADATA
		let dateElem = contents.querySelector(".flex-grow > .date");
		dateElem.textContent = "Forecasts of " + new Date(data.fcst.day_date).toLocaleDateString();

		periods.innerHTML = "";
		
		// SET OPTION ROW:

		// SET ORG RADIO BUTTON
		for (let child of contents.querySelectorAll(".orgs input")) {
			let childOrg = child.getAttribute("org");

			child.checked = childOrg == selectedOrg;

			child.onclick = () => fcstVsObsUpdate(data, contents, periods, childOrg, selectedSubOrg, selectedFcstTime)
		};
		

		// SET SUB ORG TOGGLE BAR
		let freqBar = contents.querySelector(".fcst-type-bar.fcst-freq");
		freqBar.innerHTML = "";

		let possibleSubOrgs = [];

		for (let org of Object.keys(data.fcst)) {
			if (org.startsWith(selectedOrg)) {
				possibleSubOrgs.push(org.replace(selectedOrg, ""));
			};
		};

		if ((!selectedSubOrg) || (!possibleSubOrgs.includes(selectedSubOrg))) {
			selectedSubOrg = api.random.choice(possibleSubOrgs);
		};

		for (let org of possibleSubOrgs) {
			let label = document.createElement("label");
			let thisClass = "fcst-option";

			if (org == selectedSubOrg) thisClass += " selected";
			label.textContent = (org === "3") ? "3 Hourly" : (org === "D") ? "Daily" : "Hourly";

			label.setAttribute("class", thisClass);
			freqBar.append(label);

			label.onclick = () => fcstVsObsUpdate(data, contents, periods, selectedOrg, org, selectedFcstTime);
		};

		let thisOrg = selectedOrg + selectedSubOrg;


		// SET FCST TIME BAR
		let timeBar = contents.querySelector(".fcst-type-bar.fcst-time");
		timeBar.innerHTML = "";

		let possibleTimes = Object.keys(data.fcst[thisOrg]);

		if ((!selectedFcstTime) || (!possibleTimes.includes(selectedFcstTime))) {
			selectedFcstTime = possibleTimes[0];
		};

		for (let time of possibleTimes) {
			let label = document.createElement("label");
			let thisClass = "fcst-option";

			if (time == selectedFcstTime) thisClass += " selected";
			label.textContent = api.datetime.indentifierFromDate(new Date(time));

			label.setAttribute("class", thisClass);
			timeBar.append(label);

			label.onclick = () => fcstVsObsUpdate(data, contents, periods, selectedOrg, selectedSubOrg, time);
		};


		let chosenFcstData = data.fcst[thisOrg][selectedFcstTime];


		for (let [ft, v] of Object.entries(chosenFcstData).sort( (a,b) => ( new Date(a[0]) - new Date(b[0]) ) )) {
			let elem = api.assets.fcstObsPeriodTemplate.cloneNode(true);

			fillFullFcstObsPeriod(ft, {fcst: v, obs: data.obs[ft]}, elem);

			periods.append(elem);
		};

		console.log("TODO: scroll to middle/nearest to now?")
	};


	async function pane2(locId) {
		function fillData(fcst, obs) {
			let contents = document.querySelector(".pane-2 .contents");
			let periods = document.querySelector(".pane-2 .periods");

			console.log(fcst, obs);

			fcstVsObsUpdate({fcst: fcst, obs: obs}, contents, periods);
		};

		let fcst, obs;

		api.api.getApiFcstsOfDay(locId).then((v) => {
			fcst = v;

			if (obs) fillData(fcst, obs);
		});

		api.api.getApiObsofDay(locId).then((v) => {
			obs = v;

			if (fcst) fillData(fcst, obs);
		});		
	};

	async function pane3(locId) {
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

		let monthly = await api.api.getApiMonthOfDailySummaries(FCST_TIME_BUFFER_DAYS, locId);

		let dataForCalendar = [];
		for (let [k,v] of Object.entries(monthly)) {
			v.ft = k;
			dataForCalendar.push(v);
		};

		let selector = "#local .pane-3 .calendar";

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

		let title = document.querySelector("#local .pane-3 .title-bar > .main");

		if ((counts.MO || 0) > (counts.BBC || 0)) {
			title.textContent = title.textContent.replace("[org]", "The Met Office was");

		} else if ((counts.MO || 0) < (counts.BBC || 0)) {
			title.textContent = title.textContent.replace("[org]", "BBC Weather was");

		} else {
			title.textContent = "Both organisations had the same accuracy";
		};
	};



	async function Main() {
		let searchParams = new URL(window.location.href).searchParams;
		let locId = searchParams.get("locId");

		if (!locId) {
			locId = api.random.choice(api.locIds);
			api.dom.setLocCardName(api.siteInfoDict[locId].clean_name);
		};		
		
		pane1(locId);
		pane2(locId);
		pane3(locId);

		//document.querySelector("#homepage").setAttribute("rendered", "true");

		//pane4();
	};

	Main();
})()