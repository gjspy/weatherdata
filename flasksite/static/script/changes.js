(function() {
	const CHANGES_TABLE_CONDITIONS = ["t", "f", "ws", "wt"]
	function sect1(weekData) {
		let dataForCalendar = [];
		for (let [k,v] of Object.entries(weekData)) {
			v.fcstTime = k;
			dataForCalendar.push(v);
		};

		let selector = "#changes .pane-1 .calendar";

		let today = new Date();
		let yesterdayId = api.datetime.indentifierFromDate(new Date(today.getTime() - (1000 * 60 * 60 * 24))); 

		api.dom.FillCalendar(
			selector,
			dataForCalendar,
			api.config.monthNDays,
			"regularWeeks",
			dateOnHover,
			{ [yesterdayId]: "- <i>Yesterday</i>" },
			true
		);
	};


	function sect2FillOrgCol(selector, orgData, fcstDate, count) {
		selector = selector + " table tr.";
		let selector2 = ` td:nth-of-type(${count + 1})`; // +1 bcs of cond name col

		let tdDate = document.querySelector(selector + "d" + selector2);
		tdDate.textContent = String(fcstDate.getUTCDate()).padStart(2, "0");

		for (let cond of CHANGES_TABLE_CONDITIONS) {
			let data = orgData.data[0].r["g"+cond];

			if (!data) continue;
			
			let td = document.querySelector(selector + cond + selector2);
			api.dom.setElemGrade(td, data);
		};
	};

	function sect2(weekData) {
		let selector = "#changes .pane-2 .info-tables .entry";

		let count = 0;

		for (let [fcstT, data] of Object.entries(weekData)) {
			let fcstDate = new Date(fcstT);

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
		
		document.querySelector(".sticky-bkg .background").src = `/api/weather/current-photo?loc=${locId}`;

		let weekData = await api.api.getApiWeekOfDailyResultsOfFuture("yesterday", locId);
		
		sect1(weekData);
		sect2(weekData);
		window.onresize = undefined;
		document.querySelector("#changes").setAttribute("rendered", "true");
	};

	Main();
})()