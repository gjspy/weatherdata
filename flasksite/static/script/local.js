(function() {
	const FCST_TIME_BUFFER_DAYS = 2;

	async function pane1(locId) {
		let data = (await api.api.getApiWeekOfDailySummaries(FCST_TIME_BUFFER_DAYS, locId)).data;
		let datas = Object.values(data);

		let datesInWeek = Array.from(Object.keys(data)).map( v => Date.parse(v) );

		let yesterday = datas[datesInWeek.indexOf(Math.max(...datesInWeek))];

		let yesterdayMO = api.calc.getOrgFromPeriod(yesterday, "MO");
		let yesterdayBC = api.calc.getOrgFromPeriod(yesterday, "BBC");


		let moTable = document.querySelector("#local .pane-1 #mo-summary table");
		api.dom.FillSummaryTableConditions(moTable, yesterdayMO.data[0]);

		let bbcTable = document.querySelector("#local .pane-1 #bbc-summary table");
		api.dom.FillSummaryTableConditions(bbcTable, yesterdayBC.data[0]);

		api.dom.setElemGrade(document.querySelector("#local .pane-1 #mo-summary .left-items .grade"), yesterdayMO.ga);
		api.dom.setElemGrade(document.querySelector("#local .pane-1 #bbc-summary .left-items .grade"), yesterdayBC.ga);

		let subtitle = document.querySelector("#local .pane-1 .title-bar .sub");
		subtitle.textContent = subtitle.textContent
			.replaceAll("[FCST_BUFFER_HOURS]", String(FCST_TIME_BUFFER_DAYS * 24))
			.replaceAll("[SUMMARY_DESC]", api.descriptions.SUMMARY);
	};

	function conditionalFormat(condition, v) {
		if (condition === "t") {
			if (v <= 5) return "#70ebff";
			else if (v <= 10) return "#a28800";
			else if (v <= 15) return "#f2aa00";
			else if (v < 20) return "#ec6f00";
			else return "#ec0000";
		};

		if (condition === "pr") {
			if (v > 0) return "#0025ec";
			return "#b0b0b0";
		};

		if (condition === "pp") {
			if (v >= 20) return "#0025ec";
			return "#b0b0b0";
		};
	};


	function fillHalfFcstObsPeriod(data, elem, thisOrg) {
		let wtElem = elem.querySelector(".wt");
		let tempElem = elem.querySelector(".temp");
		let windsElem = elem.querySelector(".wind .spd");
		let winddElem = elem.querySelector(".wind .dir");
		let rainElem = elem.querySelector(".rain");

		let wt = data.w;

		if (wt !== undefined) {
			if (thisOrg === "BD") {
				// because is daily summary, swap night icons to day
				
				let index = Object.values(api.nightWTsMap).indexOf(wt);
				if (index !== -1) wt = Object.keys(api.nightWTsMap)[index];
				
			} else if (api.nightWTsMap[wt]) {
				wt = api.nightWTsMap[wt];

			};

			wtElem.setAttribute("src", `https://weatherstatic.gtweb.dev/icon/100/${wt}.png`);
		};

		let t = data.t;

		if (!t && data.tm && data.tx) {
			t = Math.round(((data.tm + data.tx) / 2) * 10) / 10;
		};

		if (t) {
			tempElem.textContent = `${t}${api.units.temp}`;
			tempElem.style.color = conditionalFormat("t", t);
		};

		if (data.ws) {
			windsElem.textContent = `${data.ws} `; // ${api.units.speed}
			//windElem.style.color = conditionalFormat("ws")
		};

		if (data.wd) {
			winddElem.style.transform = `rotate(${data.wd}deg)`;
		
		} else {
			winddElem.style.display = "none";
		};
		

		if (data.pp || data.pp === 0) {
			rainElem.textContent = `${data.pp}${api.units.score}`;
			rainElem.style.color = conditionalFormat("pp", data.pp);

		} else if (data.pr) {
			rainElem.textContent = `${data.pr}${api.units.precip}`;
			rainElem.style.color = conditionalFormat("pr", data.pr);
		
		};

	};

	function fillFullFcstObsPeriod(ft, data, thisOrg, elem) {
		let ftime = new Date(ft);

		let hr = ftime.getUTCHours();

		let timeText = elem.querySelector(".time");

		if (thisOrg === "BD") timeText.textContent = "Daily Summary";
		else if (hr === 12) timeText.textContent = "12PM";
		else if (hr === 0) timeText.textContent = "12AM";
		else if (hr < 12) timeText.textContent = `${hr}AM`;
		else timeText.textContent = `${hr - 12}PM`;

		if (thisOrg === "M3") elem.classList.add("three-hr");
		else if (thisOrg === "BD") elem.classList.add("daily");
		else elem.classList.add("hourly");

		if (data.fcst) fillHalfFcstObsPeriod(data.fcst, elem.querySelector(".fcst"), thisOrg);
		if (data.obs) fillHalfFcstObsPeriod(data.obs, elem.querySelector(".obs"), thisOrg);


	};



	function selectOrgsAndTime(fcsts, selectedOrg, selectedSubOrg, selectedFcstTime) {
		if (!selectedOrg) {
			let possibleOrgs = Array.from(Object.keys(fcsts.data));
			let bdIndex = possibleOrgs.indexOf("BD"); // REMOVE BD FROM AUTOSELECT

			if (possibleOrgs.length > 1 && bdIndex !== -1) possibleOrgs.splice(bdIndex);
			
			let chosen = api.random.choice(possibleOrgs);
			selectedOrg = chosen[0];
			selectedSubOrg = chosen[1];
		};
		
		let possibleSubOrgs = [];

		for (let org of Object.keys(fcsts.data)) {
			if (!org.startsWith(selectedOrg)) continue;
			
			possibleSubOrgs.push(org.replace(selectedOrg, ""));
		};


		if ((!selectedSubOrg) || (!possibleSubOrgs.includes(selectedSubOrg))) {
			selectedSubOrg = possibleSubOrgs[0];
		};

		return [selectedOrg, selectedSubOrg, selectedFcstTime, possibleSubOrgs];
	};


	function fcstVsObsUpdate(data, contents, periods, selectedOrg, selectedSubOrg, selectedFcstTime) {
		let possibleSubOrgs;
		[selectedOrg, selectedSubOrg, selectedFcstTime, possibleSubOrgs] = selectOrgsAndTime(data.fcst, selectedOrg, selectedSubOrg, selectedFcstTime);

		// SET METADATA
		let dateElem = contents.querySelector(".option-row > .date");
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

		for (let org of possibleSubOrgs) {
			let label = document.createElement("label");
			let thisClass = "fcst-option";

			if (org == selectedSubOrg) thisClass += " selected";
			label.textContent = (org === "3") ? "3 Hourly" : (org === "D") ? "Daily" : "Hourly";

			label.setAttribute("class", thisClass);
			label.setAttribute("org", selectedOrg + org);
			freqBar.append(label);

			label.onclick = () => fcstVsObsUpdate(data, contents, periods, selectedOrg, org, selectedFcstTime);
		};


		let thisOrg = selectedOrg + selectedSubOrg;


		// SET FCST TIME BAR
		let timeBar = contents.querySelector(".fcst-type-bar.fcst-time");
		timeBar.innerHTML = "";

		let possibleTimes = Object.keys(data.fcst.data[thisOrg]);

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


		let chosenFcstData = data.fcst.data[thisOrg][selectedFcstTime];

		for (let [ft, v] of Object.entries(chosenFcstData).sort( (a,b) => ( new Date(a[0]) - new Date(b[0]) ) )) {
			let elem = api.assets.fcstObsPeriodTemplate.cloneNode(true);

			let obsToUse = data.obs[ft];

			if (thisOrg === "BD") {
				obsToUse = api.calc.getAvgObs(Object.values(data.obs));
			};

			fillFullFcstObsPeriod(ft, {fcst: v, obs: obsToUse}, thisOrg, elem);

			periods.append(elem);
		};

		setTimeout(() => {
			let bounds = periods.getBoundingClientRect();

			periods.scroll(
				(periods.scrollWidth / 2) - (bounds.width / 2),
				0
			);
		}, 100);
	};


	async function pane2(locId) {
		function fillData(fcst, obs) {
			let contents = document.querySelector(".pane-2 .contents");
			let periods = document.querySelector(".pane-2 .periods");

			fcstVsObsUpdate({fcst: fcst, obs: obs}, contents, periods);
		};

		Promise.all([
			api.api.getApiFcstsOfDay(locId),
			api.api.getApiObsofDay(locId)
		]).then((values) => {
			fillData(values[0], values[1]);
		});
	};


	async function pane3(locId) {
		function dateOnHover(dateElemHoveringOver, period, dt, calendarCont, bestOrg, bestGrade) {
			if (bestOrg === "EQUALS") return;

			let calendar = calendarCont.offsetParent;

			if (calendar.querySelector(".date[floating=\"true\"]")) return;

			let floatElem = api.dom.fillOneGradeDateElem(period, dt, calendarCont, true);

			floatElem.querySelector(".datetxt").remove();

			// boundingRect() returns global space, need to calculate relative
			let calBounds = calendar.getBoundingClientRect(); 
			let bounds = dateElemHoveringOver.getBoundingClientRect();

			floatElem.style.position = "absolute";
			floatElem.style.top = String((bounds.top - calBounds.top - 2) + bounds.height) + "px";
			floatElem.style.left = String(bounds.left - calBounds.left - 1) + "px";
			floatElem.style["z-index"] = "101";
			//floatElem.style.opacity = "0";
			
			floatElem.setAttribute("floating", "true");

			setTimeout(() => {
				floatElem.style.opacity = "1";
			});
			
			dateElemHoveringOver.addEventListener("mouseleave", () => {
				floatElem.setAttribute("floating", "false");
				floatElem.style.opacity = "0";

				setTimeout(() => {
					floatElem.remove();
				}, 300);
			});
		};

		let monthly = (await api.api.getApiMonthOfDailySummaries(FCST_TIME_BUFFER_DAYS, locId)).data;

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
		);

		let elems = document.querySelectorAll(selector + " .calendar-cont > *");
		let counts = {};

		for (let elem of elems) {
			let v = elem.getAttribute("best");
			if (!v || v === "EQUALS") continue;

			if (!counts[v]) counts[v] = 0;
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
		
		document.querySelector(".sticky-bkg .background").src = `/api/weather/current-photo?loc=${locId}`;
		
		pane1(locId).then((v) => {
			document.querySelector("#local").setAttribute("rendered", "true");
		});

		pane2(locId);
		pane3(locId);

		window.onresize = undefined;
	};

	Main();
})();