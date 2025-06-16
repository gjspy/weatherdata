(function() {
	const CHANGES_TABLE_CONDITIONS = ["t", "f", "ws", "w"]
	function sect1(dataForCalendar, locId) {
		dataForCalendar = dataForCalendar.slice(-7);

		let selector = "#changes .sect-1 .calendar";

		document.querySelector("#changes .sect-1 .title-bar .right-items .main").textContent = api.siteInfoDict[locId].clean_name;

		let yesterday = new Date((new Date()).getTime() - (1000 * 60 * 60 * 24));
		//let yesterdayId = api.datetime.indentifierFromDate(yesterday); 

		api.dom.FillCalendar(
			selector,
			dataForCalendar,
			7,
			"dynamicWeeksWithGaps",
			undefined,
			{},//{ [yesterdayId]: "- <i>Yesterday</i>" },
			true
		);

		for (let elem of document.querySelectorAll(selector + " .calendar-cont .date")) {
			let dateDiff = yesterday - elem.__data.dt;

			let days = (new Date(dateDiff)).getUTCDate();

			let dateTxt = (days === 1) ? "On the day" : String(days) + " days prior";
			elem.querySelector(".datetxt").textContent += ` (${dateTxt})`;
		};
	};


	function sect2FillOrgCol(selector, orgData, fcstDate, count) {
		selector = selector + " table tr.";
		let selector2 = ` td:nth-of-type(${count + 2})`; // +1 bcs of cond name col

		let tdDate = document.querySelector(selector + "d" + selector2);
		tdDate.textContent = String(fcstDate.getUTCDate()).padStart(2, "0") + " " + api.datetime.months[fcstDate.getUTCMonth()];

		for (let cond of CHANGES_TABLE_CONDITIONS) {
			let data = orgData.data[0].r["g"+cond];

			if (!data) continue;
			
			let td = document.querySelector(selector + cond + selector2);
			api.dom.setElemGrade(td, data);
		};
	};

	function sect2(dataForCalendar) {
		let selector = "#changes .sect-2 .info-tables .entry";

		dataForCalendar = dataForCalendar.slice(-5);

		let count = 0;

		for (let data of dataForCalendar) {
			let fcstDate = new Date(data.ft);

			let bcData = api.calc.getOrgFromPeriod(data, "BBC");
			let moData = api.calc.getOrgFromPeriod(data, "MO");

			sect2FillOrgCol(selector + ".bbc", bcData, fcstDate, count);
			sect2FillOrgCol(selector + ".mo", moData, fcstDate, count);

			count ++;
		};
	};



	async function Main() {
		let searchParams = new URL(window.location.href).searchParams;
		let locId = searchParams.get("locId");

		if (!locId) {
			locId = api.random.choice(api.locIds);
			api.dom.setLocCardName(api.siteInfoDict[locId].clean_name);
		};

		let weekData = (await api.api.getApiWeekOfDailyResultsOfFuture("yesterday", locId)).data;

		let dataForCalendar = [];
		for (let [k,v] of Object.entries(weekData)) {
			v.ft = k;
			dataForCalendar.push(v);
		};

		dataForCalendar = dataForCalendar.sort((a, b) => (new Date(a.ft) - new Date(b.ft)));
		
		sect1(dataForCalendar, locId);
		sect2(dataForCalendar);
		window.onresize = undefined;
		document.querySelector("#changes").setAttribute("rendered", "true");
	};

	Main();
})()