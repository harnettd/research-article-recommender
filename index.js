const nameInput = document.querySelector('#name')
const nameInputErrMsg = document.querySelector('.author-name__err')
const btnSubmit = document.querySelector('#btn-submit')
const recommendationsList = document.querySelector('#recommendations-list')

// When the webpage loads, clear the value of nameInput and 
// hide its error message.
nameInput.value = ''
nameInputErrMsg.classList.remove('author-name__err--on-err')

// Delete all li elements in recommendationsList.
const deleteListItems = () => {
    const listItems = recommendationsList.querySelectorAll('li')
    listItems.forEach(listItem => {
        recommendationsList.removeChild(listItem)
    })
}

// Given a DOI, create a new li element in recommendationsList.
// The innerHTML of the new li element is a link to the DOI in question.
// Add all necessary classes as well.
const createNewListItem = doi => {
    const newListItem = document.createElement('li')
    const newLink = document.createElement('a')
    recommendationsList.appendChild(newListItem)
    newListItem.appendChild(newLink)
    
    newLink.innerText = doi
    newLink.setAttribute('href', `https://doi.org/${doi}`)
    newLink.setAttribute('target', '_blank')

    newListItem.classList.add('recommendations-list__recommendation')
    newLink.classList.add('recommendations-list__link')
}

//  Fetch a list of authors in the recommender's dataset.
// const apiURL = 'http://127.0.0.1:5000'
const apiURL = 'https://capstone-article-recommender-3e41bcce122c.herokuapp.com'
const authorsRoute = 'authors'
const url = `${apiURL}/${authorsRoute}`

fetch(url, {
    headers: { 'Content-Type': 'application/json' }
})
    .then(res => {
        // Check if response's HTTP status code is not 200.
        if (res.status != 200) {
            console.log('Fetch authors failed,', res.status)
            return
        }
        // The response HTTP status code *is* 200.
        return res.json()
    })
    .then(data => {
        // an array of all authors in the dataset
        const authors = data.authors
        console.log(authors)

        // Add an event listener to the SUBMIT button that 
        // takes the name of an author and fetches an array
        // of recommended articles.
        btnSubmit.addEventListener('click', (evt) => {
            evt.preventDefault()

            const recommendationsRoute = 'recommendations'
            const url = `${apiURL}/${recommendationsRoute}`
            const author = nameInput.value
            
            // Check if author is in authors.
            if (authors.indexOf(author) == -1) {
                nameInputErrMsg.classList.add('author-name__err--on-err')
                return
            }

            // The author *is* in authors.
            nameInputErrMsg.classList.remove('author-name__err--on-err')
            const data = { 'author': author }

            // Fetch an array of article recommendations.
            fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
                .then(res => {
                    // Check if response's HTTP status code is not 200.
                    if (res.status != 200) {
                        console.log('Fetch authors failed,', res.status)
                        return
                    }
                    // The response HTTP status code *is* 200.
                    return res.json()
                })
                .then(data => {
                    const recommendations = data.recommendations 
                    deleteListItems()
                    recommendations.forEach(doi => { 
                        createNewListItem(doi) 
                    })                  
                })
                .catch(err => { console.error('Fetch recommendations error,', err) })
        })
    })
    .catch((err) => { console.error('Fetch authors error,', err) })
