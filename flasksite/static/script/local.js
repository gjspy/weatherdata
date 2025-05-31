(function() {


	function pane1(data) {
		let moTable = document.querySelector("#homepage .pane-2 #mo-summary table");
		api.dom.FillSummaryTableConditions(moTable, data.mo);

		let bbcTable = document.querySelector("#homepage .pane-2 #bbc-summary table");
		api.dom.FillSummaryTableConditions(bbcTable, data.bbc);

		api.dom.setElemGrade(document.querySelector("#homepage .pane-2 #mo-summary > label.grade"), (data.mo || {}).ga);
		api.dom.setElemGrade(document.querySelector("#homepage .pane-2 #bbc-summary > label.grade"), (data.bbc || {}).ga);
	};



	function fillHalfFcstObsPeriod(data, elem) {
		let wtElem = elem.querySelector(".wt");
		let tempElem = elem.querySelector(".temp");
		let windElem = elem.querySelector(".wind");
		let rainElem = elem.querySelector(".rain");

		if (data.w) {
			wtElem.setAttribute("src", `/static/icon/100/${data.w}.png`);

		} else {
			wtElem.style.opacity = "0";
		};

		if (data.t) tempElem.textContent = `${data.t}${api.units.temp}`;
		else if (data.tm && data.tx) tempElem.textContent = `${data.tm} - ${data.tx}${api.units.temp}`;
		else tempElem.style.display = "none";

		if (data.ws) windElem.textContent = `${data.ws}${api.units.speed}`;
		else windElem.style.display = "none";

		if (data.pp) rainElem.textContent = `${data.pp}${api.units.score}`;
		else if (data.pr) rainElem.textContent = `${data.pr}${api.units.precip}`;
		else rainElem.style.display = "none";

	};

	function fillFullFcstObsPeriod(ft, data, elem) {
		let ftime = new Date(ft);

		console.log(data);

		let hr = ftime.getUTCHours();

		let timeText = elem.querySelector(".time");

		if (hr === 12) timeText.textContent = "12PM";
		else if (hr === 0) timeText.textContent = "12AM";
		else if (hr < 12) timeText.textContent = `${hr}AM`;
		else timeText.textContent = `${hr - 12}PM`;

		console.log(hr, timeText.textContent);

		if (data.fcst) fillHalfFcstObsPeriod(data.fcst, elem.querySelector(".fcst"));
		if (data.obs) fillHalfFcstObsPeriod(data.obs, elem.querySelector(".obs"));

	};


	function fcstVsObsUpdate(data, optionRow, periods, selectedOrg, selectedSubOrg, selectedFcstTime) {
		if (!selectedOrg) {
			let chosen = api.random.choice(Object.keys(data.fcst));
			selectedOrg = chosen[0];
			selectedSubOrg = chosen[1];
		};

		periods.innerHTML = "";
		
		// SET OPTION ROW

		// SET ORG RADIO BUTTON
		for (let child of optionRow.querySelectorAll(".orgs input")) {
			let childOrg = child.getAttribute("org");

			child.checked = childOrg == selectedOrg;

			child.onclick = () => fcstVsObsUpdate(data, optionRow, periods, childOrg, selectedSubOrg, selectedFcstTime)
		};
		

		// SET SUB ORG TOGGLE BAR
		let freqBar = optionRow.querySelector(".fcst-type-bar.fcst-freq");
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

			label.onclick = () => fcstVsObsUpdate(data, optionRow, periods, selectedOrg, org, selectedFcstTime);
		};

		let thisOrg = selectedOrg + selectedSubOrg;


		// SET FCST TIME BAR
		let timeBar = optionRow.querySelector(".fcst-type-bar.fcst-time");
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

			label.onclick = () => fcstVsObsUpdate(data, optionRow, periods, selectedOrg, selectedSubOrg, time);
		};




		let chosenFcstData = data.fcst[thisOrg][selectedFcstTime];
		let thisObs = data.obs;

		console.log(selectedOrg, selectedSubOrg, selectedFcstTime, chosenFcstData, Object.entries(chosenFcstData));


		for (let [ft, v] of Object.entries(chosenFcstData).sort( (a,b) => ( new Date(a[0]) - new Date(b[0]) ) )) {
			let elem = api.assets.fcstObsPeriodTemplate.cloneNode(true);
			console.log(ft, v);
			fillFullFcstObsPeriod(ft, {fcst: v, obs: thisObs[ft]}, elem);

			periods.append(elem);
		};

		console.log("TODO: scroll to middle/nearest to now?")
	};


	async function pane2(locId) {
		let fcsts = await api.api.getApiFcstsOfDay(locId);
		let obs = {};

		let optionRow = document.querySelector(".pane-2 .option-row");
		let periods = document.querySelector(".pane-2 .periods");

		fcstVsObsUpdate({fcst: fcsts, obs: obs}, optionRow, periods);
	};



	async function Main() {
		let searchParams = new URL(window.location.href).searchParams;
		let locId = searchParams.get("locId");

		if (!locId) {
			locId = api.random.choice(api.locIds);
			api.dom.setLocCardName(api.siteInfoDict[locId].clean_name);
		};		
		
		pane2(locId);
		//pane3(weekDataForCalendar, bestOverWeek);

		//document.querySelector("#homepage").setAttribute("rendered", "true");

		//pane4();
	};

	Main();
})()