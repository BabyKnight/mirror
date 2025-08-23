//main js

function reloadContent(url){
	const contentDiv = document.getElementById('main-content');

    fetch(url)
       .then(response =>{
           if (!response.ok){
               throw new Error('Network response was not ok');
           }
           return response.text();
       })
       .then(html => {
           contentDiv.innerHTML = html;
        })
}

function clearAllSt(element){
	element.classList.forEach( cls => {
		if (/^bg-/.test(cls)){
			element.classList.remove(cls);
		}
	})
}

function refreshSplSt(){
	const stElems = document.getElementsByClassName('splSt')

	for (const stEl of stElems){
		splId = stEl.getAttribute('splId')
		url = `/api/search?q=spl&id=${splId}`
		fetch(url)
       		.then(response =>{
           		if (!response.ok){
               		throw new Error('Network response was not ok');
           		}
           		return response.json();
       		})
       		.then(data => {
           		const st = data['data']['status_code']
           		clearAllSt(stEl)
           		if (st == '00') {
           			stEl.classList.add('bg-gray-300')
           		}else if(st == '10'){
           			stEl.classList.add('bg-green-300')
           		}else if(st == '11' || st == '12' || st == '13'){
           			stEl.classList.add('bg-red-500')
           		}else{
           			stEl.classList.add('bg-yellow-500')
           		}
        	})
	}
}

function refreshTskSt(){
	const stElems = document.getElementsByClassName('tskSt')

	for (const stEl of stElems){
		tskId = stEl.getAttribute('tskId')
		url = `/api/search?q=tsk&id=${tskId}`
		fetch(url)
       		.then(response =>{
           		if (!response.ok){
               		throw new Error('Network response was not ok');
           		}
           		return response.json();
       		})
       		.then(data => {
           		const st = data['data']['task_status_code']
           		clearAllSt(stEl)

           		if (st == '11') {
           			stEl.classList.add('bg-yellow-500')
           		}else if(st == '12'){
           			stEl.classList.add('bg-red-500')
           		}else if(st == '13'){
           			stEl.classList.add('bg-green-500')
           		}else if(st == '14'){
           			stEl.classList.add('bg-gray-600')
           		}else{
           			stEl.classList.add('bg-gray-200')
           		}
        	})
	}
}

function showMsg(msg, type){
    const msgBox = document.getElementById('msgBox')

    msgBox.className = "fixed top-0 left-1/2 transform -translate-x-1/2 mt-4 w-96 p-4 rounded-xl shadow-lg text-white text-center transition-all duration-500 ease-in-out"
    msgBox.textContent = msg

    if (type === 'success'){
        msgBox.classList.add('bg-green-500');
    }else{
        msgBox.classList.add('bg-red-500');
    }

    msgBox.classList.remove('opacity-0', '-translate-y-20');
    msgBox.classList.add('opacity-100', 'translate-y-0');

    setTimeout(() => {
        msgBox.classList.remove('opacity-100', 'translate-y-0');
        msgBox.classList.add('opacity-0', '-translate-y-20');
    }, 5000);
}

document.addEventListener('DOMContentLoaded', function(){
    const links = document.querySelectorAll('.nav-link');
    const contentDiv = document.getElementById('main-content');

    links.forEach(link => {
        link.addEventListener('click', function(event){
            const currentActiveLink = document.getElementsByClassName('nav-act')[0];
            currentActiveLink.classList.add('nav-deact');
            currentActiveLink.classList.remove('nav-act');
            event.target.closest('div').classList.add('nav-act');
            event.target.closest('div').classList.remove('nav-deact');
            event.preventDefault();
            const url = this.getAttribute('data-url');

            fetch(url)
                .then(response =>{
                    if (!response.ok){
                        throw new Error('Network response was not ok');
                    }
                    return response.text();
                })
                .then(html => {
                    contentDiv.innerHTML = html;
                    if(url == '/index/dashboard/'){
                        // dynamically render the charts in dashboard
                        renderChartsInDashboard()
                    }
                    if(url == '/index/task/'){
                        // add function to listen radio change
                        const taskCatRadio = document.querySelectorAll('input[name="taskCategory"]')
                        const installLabel = document.getElementsByClassName('tsk-cat-label-i')[0]
                        const testLabel = document.getElementsByClassName('tsk-cat-label-t')[0]
                        const combLabel = document.getElementsByClassName('tsk-cat-label-c')[0]
                        taskCatRadio.forEach(radio => {
                            radio.addEventListener('change', () => {
                                if (radio.checked) {
                                    if ( radio.id === "installOnly"){
                                        document.getElementById('image').disabled = false
                                    }
                                    else if ( radio.id === "combination"){
                                        document.getElementById('image').disabled = false
                                    }
                                    else{
                                        document.getElementById('image').selectedIndex = 0
                                        document.getElementById('image').disabled = true
                                    }

                                    taskCatRadio.forEach(i => {
                                        i.closest('label').classList.remove('border-blue-700')
                                        i.closest('label').classList.add('border-grey-300')
                                    });
                                    radio.closest('label').classList.remove('border-grey-300')
                                    radio.closest('label').classList.add('border-blue-700')
                                }
                            });
                        });
						setInterval(refreshTskSt, 10000);
                    }
                    if(url == '/index/sample/'){
                    	setInterval(refreshSplSt, 10000);
                    }
                })
                .catch(error => {
                    contentDiv.innerHTML = "<p class='text-red-500'>Error loading content. </p>";
                });
        });
    });

    contentDiv.addEventListener('click', function(e){
        const clickedButton = e.target.closest('.action-btn');  

        if(clickedButton){
            e.preventDefault(); 

            const actionEvt = clickedButton.dataset.action;
            const actionId = clickedButton.dataset.actionId;    

            if(actionEvt === 'showAddSplPanel'){
                const addSplPanel = document.getElementById('spl-add-panel');
                const addSplForm = document.getElementById('addSplForm');
                addSplForm.reset();
                addSplPanel.classList.remove('hidden')
            }else if(actionEvt === 'hideAddSplPanel'){
                const addSplPanel = document.getElementById('spl-add-panel');
                addSplPanel.classList.add('hidden')
            }else if(actionEvt === 'submitAddSplForm'){
                const addSplForm = document.getElementById('addSplForm');   
                const requiredInputs = addSplForm.querySelectorAll('[data-required]');
                let allFieldValid = true
                requiredInputs.forEach(input => {
                    if (input.value.trim() === ''){
                        input.classList.add('text-red-500');
                        input.classList.remove('text-grey-700')
                        allFieldValid = false
                    }else{
                        input.classList.remove('text-red-500');
                        input.classList.add('text-grey-800')
                    }
                });
                if (allFieldValid){
                    const formData = new FormData(addSplForm);      

                    const csrfToken = formData.get('csrfmiddlewaretoken');
                    if(!csrfToken){
                        alert('csrf token error')
                    }
                    fetch(addSplForm.action, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,
                        },
                        body: formData,
                    })
                    .then(response =>{
                        if(response.ok){
                            const addSplPanel = document.getElementById('spl-add-panel');
                            addSplPanel.classList.add('hidden')
                            addSplForm.reset();
                            reloadContent('/index/sample?rfna=1')
                            showMsg("Sample has been registered successfully!", 'success');
                        }
                        else{
                            showMsg("Some error occured when registering the sample!", 'error');
                        }
                    })
                }else{
                    showMsg("Please enter all required fields!", 'error');
                }
            }else if(actionEvt === 'showAddTskPanel'){
                const addSplPanel = document.getElementById('tsk-add-panel');
                const addSplForm = document.getElementById('addTskForm');
                addSplForm.reset();
                addSplPanel.classList.remove('hidden')
            }else if(actionEvt === 'hideAddTskPanel'){
                const addSplPanel = document.getElementById('tsk-add-panel');
                addSplPanel.classList.add('hidden')
            }else if(actionEvt === 'cancelTask'){
                tskId = clickedButton.getAttribute('value')
                url = `/api/task/cancel?id=${tskId}`
                fetch(url, {
                    method: "GET"
                })
                .then(response => response.text())
                .then(data => {
                    reloadContent('/index/task/')
                    showMsg("Task cancelled successfully!", 'success');
                })
            }else if(actionEvt === 'submitAddTskForm'){
                const addTskForm = document.getElementById('addTskForm');
                const requiredInputs = addTskForm.querySelectorAll('[data-required]');
                let allFieldValid = true
                let tcValid = false
                requiredInputs.forEach(input => {
                    if (input.id === 'tc'){
                        const tcRequired = addTskForm.querySelectorAll('[tc-required]');

                        tcRequired.forEach(tc => {
                            if (tc.checked){
                                tcValid = true
                            }
                        })
                    }else{  
                        if (input.value.trim() === ''){
                            input.classList.add('text-red-500');
                            input.classList.remove('text-grey-700')
                            allFieldValid = false
                        }else{
                            input.classList.remove('text-red-500');
                            input.classList.add('text-grey-800')
                        }
                    }
                });

                if (!tcValid){
                    allFieldValid = false
                    const tcLabel = document.getElementById('tc');
                    tcLabel.classList.add('text-red-500');
                    tcLabel.classList.remove('text-grey-700')
                }else{
                    const tcLabel = document.getElementById('tc');
                    tcLabel.classList.remove('text-red-500');
                    tcLabel.classList.add('text-grey-700')
                }

                if (allFieldValid){
                    const formData = new FormData(addTskForm);      

                    const csrfToken = formData.get('csrfmiddlewaretoken');
                    if(!csrfToken){
                        alert('csrf token error')
                    }
                    fetch(addTskForm.action, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,       

                        },
                        body: formData,
                    })
                    .then(response =>{
                        if(response.ok){
                            const addTskPanel = document.getElementById('tsk-add-panel');
                            addTskPanel.classList.add('hidden')
                            addTskForm.reset();
                            reloadContent('/index/task/')
                            showMsg("Task has been added successfully!", 'success');
                        }
                    })
                }else{
                    showMsg("Please enter all required fields!", 'error');
                }
            }
        }
    })

});


/* for index & dashboard charts loading */
    function renderDashboardTaskCountChart(){
        // chart for task count
        const taskCountCtx = document.getElementById('taskCountChart').getContext('2d');
        let taskCountChart;
    
        function renderTaskCountChart(){
            fetch("/api/charts_data/task_st_this_week")
            .then(response =>{
                if (!response.ok){
                    throw new Error('Charts data error')
                }
                return response.json();
            })
            .then(data => {
                console.log('retrive data success', data);
                taskCountData = data
                if (taskCountChart) {
                    taskCountChart.destory();
                }
    
                taskCountChart = new Chart(taskCountCtx, {
                    type: 'line',
                    data: {
                        labels: taskCountData['label'],
                        datasets: [{
                            label: 'Task Created: ',
                            data: taskCountData['dataset'],
                            borderColor: '#6366F1',
                            backgroundColor: 'rgba(99, 102, 241, 0.2)',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            x: { grid: { display: false } },
                            y: { grid: { color: '#f1f5f9' }, beginAtZero: true }
                        }
                    }
                })

            })
            .catch(error => {
                console.error('retrive data error', error)
            });
        }
        renderTaskCountChart()
    }

    function renderDashboardImageReleasedChart(){
        //  chart for image release statistics
        const imgReleaseCtx = document.getElementById('imageCatChart').getContext('2d');
        let imageReleaseChart;
        function renderImageReleasedChart(){
            fetch("/api/charts_data/image")
            .then(response =>{
                if (!response.ok){
                    throw new Error('Charts data error')
                }
                return response.json();
            })
            .then(data => {
                console.log('retrive data success', data);
                imgReleaseData = data
                if (imageReleaseChart) {
                    imageReleaseChart.destory();
                }
    
                imageReleaseChart = new Chart(imgReleaseCtx, {
                    type: 'bar',
                    data: {
                        labels: imgReleaseData['label'],
                        datasets: [{
                            label: 'Edge',
                            data: imgReleaseData['dataset']['edge'],
                            backgroundColor: '#6366F1'
                        },
                        {
                            label: 'Next',
                            data: imgReleaseData['dataset']['next'],
                            backgroundColor: '#F87171'
                        },
                        {
                            label: 'Proposed',
                            data: imgReleaseData['dataset']['proposed'],
                            backgroundColor: '#34D399'
                        },
                        {
                            label: 'Production',
                            data: imgReleaseData['dataset']['production'],
                            backgroundColor: '#8B5CF6'
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            x: { grid: { display: false } },
                            y: { grid: { color: '#f1f5f9' }, beginAtZero: true }
                        }
                    }
                })
                
            })
            .catch(error => {
                console.error('retrive data error', error)
            });
        }
        renderImageReleasedChart()
    }

    function renderDashboardTaskSummaryChart(){
        // chart for task summary data
        const taskSumCtx = document.getElementById('taskSummaryChart').getContext('2d');
        let taskSumChart;
        function renderTaskSummaryChart(){
            fetch("/api/charts_data/task_result_sum")
            .then(response =>{
                if (!response.ok){
                    throw new Error('Charts data error')
                }
                return response.json();
            })
            .then(data => {
                console.log('retrive data success', data);
                tskSumChartData = data
                if (taskSumChart) {
                    taskSumChart.destory();
                }
    
                taskSumChart = new Chart(taskSumCtx, {
                    type: 'bar',
                    data: {
                        labels: tskSumChartData['label'],
                        datasets: [
                        {
                            label: 'Installation Passed',
                            data: tskSumChartData['dataset']['i']['pass'],
                            backgroundColor: ['#60A5FA']
                        },
                        {
                            label: 'Checkbox Passed',
                            data: tskSumChartData['dataset']['t']['pass'].map(num => -Math.abs(num)),
                            backgroundColor: ['#F87171']
                        },
                        {
                            label: 'Installation Failed',
                            data: tskSumChartData['dataset']['i']['fail'],
                            backgroundColor: ['#60A5FA']
                        },
                        {
                            label: 'Checkbox Failed',
                            data: tskSumChartData['dataset']['t']['fail'].map(num => -Math.abs(num)),
                            backgroundColor: ['#F87171']
                        },
                        ]
                    },
                    options: {
                        indexAxis: 'x',  // <-- This makes it horizontal
                        responsive: true,
                        plugins: {
                            legend: { display: false}
                        },
                        scales: {
                            x: {
                                beginAtZero: true
                            }
                        }
                    }
                })
                
            })
            .catch(error => {
                console.error('retrive data error', error)
            });
        }
        renderTaskSummaryChart()
    }

    function renderDashboardSampleStChart(){

        // chart for sample statistics data
        const platStCtx = document.getElementById('sampleStChart').getContext('2d'); 


        let splStatisticsChart;
        function renderSampleStatisticsChart(){
            fetch("/api/charts_data/sample_statistics")
            .then(response =>{
                if (!response.ok){
                    throw new Error('Charts data error')
                }
                return response.json();
            })
            .then(data => {
                console.log('retrive data success', data);
                splStChartData = data['dataset']
                if (splStatisticsChart) {
                    splStatisticsChart.destory();
                }
    
                splStatisticsChart = new Chart(platStCtx, {
                    type: 'doughnut',
                    data: {
                        labels: ['EVT', 'DVT', 'DVT1', 'DVT2', 'ENG Regression', 'Other'],
                        datasets: [{
                            data: [
                                splStChartData['EVT'], 
                                splStChartData['DVT'], 
                                splStChartData['DVT1'], 
                                splStChartData['DVT2'], 
                                splStChartData['PILOT'], 
                                splStChartData['Unknown'], 
                            ],
                            backgroundColor: ['#FF6B6B','#FFD166','#06D6A0','#118AB2','#6A4C93','#DFDFDF']
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: { display: false }
                        }
                    }
                })
                
            })
            .catch(error => {
                console.error('retrive data error', error)
            });
        }
        renderSampleStatisticsChart()
    }

    function renderChartsInDashboard(){
        renderDashboardTaskCountChart()
        renderDashboardImageReleasedChart()
        renderDashboardTaskSummaryChart()
        renderDashboardSampleStChart()
    }

    document.addEventListener('DOMContentLoaded', function(){
        renderChartsInDashboard()
    });
