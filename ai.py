from openai import OpenAI
from dataclasses import dataclass
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from web_drivers import web_driver

@dataclass
class Preferences:
    description: str

def get_llm():
    client = OpenAI(
        base_url=os.getenv('LM_STUDIO_URL'),
        api_key=os.getenv('LM_STUDIO_API_KEY')
    )
    return client

def scrape_detailed_data(url: str) -> dict:
    try:
        if 'storia.ro' in url:
            print("\nScraping from Storia...")
            driver = web_driver.get_driver()
            try:
                driver.get(url)
                # Wait for the description element to be present
                wait = WebDriverWait(driver, 10)
                description_element = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-cy="adPageAdDescription"] span'))
                )
                description_text = description_element.text
                
            finally:
                driver.quit()
                
        elif 'olx.ro' in url:  # OLX
            print("Scraping from OLX...")
            driver = web_driver.get_driver()
            try:
                driver.get(url)
                wait = WebDriverWait(driver, 10)
                
                description_element = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-cy="ad_description"] div.css-19duwlz'))
                )
                description_text = description_element.text
                
                parameters = {}
                
                try:
                    seller_element = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="ad-parameters-container"] p.css-1los5bp'))
                    )
                    parameters['seller_type'] = seller_element.text
                except:
                    parameters['seller_type'] = 'Unknown'
                
                try:
                    params_container = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="ad-parameters-container"]'))
                    )
                    param_elements = params_container.find_elements(By.CSS_SELECTOR, 'p.css-1los5bp')
                    
                    for param in param_elements:
                        text = param.text.strip()
                        if ':' in text:
                            key, value = text.split(':', 1)
                            parameters[key.strip()] = value.strip()
                        else:
                            # Handle cases without colon (like "Persoana fizica")
                            parameters[text] = True
                except:
                    pass
                
                features = {}
                try:
                    feature_sections = wait.until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid="ad-features"]'))
                    )
                    for section in feature_sections:
                        try:
                            section_name = section.find_element(By.CSS_SELECTOR, 'h3').text
                            feature_elements = section.find_elements(By.CSS_SELECTOR, 'li')
                            section_features = [feature.text for feature in feature_elements]
                            
                            if section_features:
                                features[section_name] = section_features
                        except:
                            continue
                except:
                    pass
                
                if features:
                    parameters['Features'] = features
                
            finally:
                driver.quit()
                
        elif 'autovit.ro' in url:  # Autovit
            print("Scraping from Autovit...")
            driver = web_driver.get_driver()
            try:
                driver.get(url)
                wait = WebDriverWait(driver, 10)
                
                description_element = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="textWrapper"]'))
                )
                description_text = wait.until(
                    lambda d: description_element.text if description_element.is_displayed() else ""
                )
                
                parameters = {}
                
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        seller_element = wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '.ooa-70qvj9 .ooa-1hl3hwd'))
                        )
                        parameters['seller_type'] = seller_element.text
                        break
                    except:
                        if attempt == max_retries - 1:
                            parameters['seller_type'] = 'Unknown'
                
                try:
                    basic_info = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="basic_information"]'))
                    )
                    info_elements = basic_info.find_elements(By.CSS_SELECTOR, '[data-testid]')
                    for element in info_elements:
                        try:
                            label = wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, '.eur4qwl8'))
                            ).text
                            value = wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, '.eur4qwl9'))
                            ).text
                            parameters[label] = value
                        except:
                            continue
                except:
                    pass
                
                try:
                    tech_specs = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="collapsible-groups-wrapper"]'))
                    )
                    spec_elements = tech_specs.find_elements(By.CSS_SELECTOR, '[data-testid]')
                    for element in spec_elements:
                        try:
                            label = wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, '.eur4qwl8'))
                            ).text
                            value = wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, '.eur4qwl9'))
                            ).text
                            parameters[label] = value
                        except:
                            continue
                except:
                    pass
                
                features = {}
                try:
                    feature_sections = wait.until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.ooa-xve46n button'))
                    )
                    for section in feature_sections:
                        try:
                            # Get section name
                            section_name = wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, '.e1jq34to3'))
                            ).text
                            
                            # Click to expand section if needed
                            if section.get_attribute('aria-expanded') == 'false':
                                driver.execute_script("arguments[0].click();", section)
                                time.sleep(0.5)  # Wait for animation
                            
                            # Get features in this section
                            section_features = []
                            feature_elements = wait.until(
                                EC.presence_of_all_elements_located((By.XPATH, "following-sibling::div//p[contains(@class, 'e1jq34to3')]"))
                            )
                            for feature in feature_elements:
                                section_features.append(feature.text)
                            
                            if section_features:
                                features[section_name] = section_features
                        except:
                            continue
                except:
                    pass
                
                if features:
                    parameters['Dotari'] = features
                
            finally:
                driver.quit()
                
        else:
            print(f"Unsupported website: {url}")
            description_text = ""
            parameters = {}
        
        details = {
            'description': description_text,
            'parameters': parameters
        }
        
        return details
            
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        import traceback
        print("Full error:", traceback.format_exc())
        return None

def calculate_rating(listing, details: dict, preferences: Preferences, llm):
    # Define the rating tool
    tools = [
        {
            "type": "function",
            "function": {
                "name": "rate_car",
                "description": "Rates a car listing based on user preferences and provides reasoning",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "rating": {
                            "type": "number",
                            "description": "Rating from 0 to 10, where 10 is a perfect match"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Detailed explanation of why the car was rated this way, including specific details about the car's condition, features, and how it matches the requirements"
                        }
                    },
                    "required": ["rating", "reasoning"]
                }
            }
        }
    ]
    
    # Extract car-specific information from the listing
    age = listing[7] if len(listing) > 7 else None
    kilometers = listing[8] if len(listing) > 8 else None
    
    # Format additional parameters for the prompt
    params_text = ""
    if 'parameters' in details and details['parameters']:
        params_text = "\nAdditional Parameters:\n"
        for key, value in details['parameters'].items():
            if isinstance(value, bool):
                params_text += f"- {key}\n"
            else:
                params_text += f"- {key}: {value}\n"
    
    user_prompt = f"""Rate this car from 0 to 10 based on these requirements:
    {preferences.description}

    Car details:
    Title: {listing[0]}
    Price: {listing[2]} EUR
    Location: {listing[4]}
    Age: {age} years
    Kilometers: {kilometers} km
    {params_text}
    
    Additional description:
    {details['description']}
    
    Please provide unique perspectives in your reasoning, focusing on different aspects of the car.
    """

    try:
        completion = llm.chat.completions.create(
            model=os.getenv('LM_STUDIO_MODEL'),
            messages=[
                {"role": "system", "content": "You are an AI that rates car listings based on user preferences. Each rating should provide a unique perspective, focusing on different aspects of the car."},
                {"role": "user", "content": user_prompt}
            ],
            tools=tools,
            tool_choice="required",  # Force the use of tools
            temperature=0.4,
            max_tokens=500,  # Reduced max tokens to prevent excessive generation
        )
        
        # Check if we got a response with tool calls
        if not completion.choices[0].message.tool_calls:
            print("Warning: AI did not return a tool call, falling back to text response")
            # Fall back to parsing the text response
            response_text = completion.choices[0].message.content.strip()
            rating_pattern = re.search(r'Rating:\s*(\d+(?:\.\d+)?)', response_text)
            reasoning_pattern = re.search(r'Reasoning:\s*(.*)', response_text)
            
            if rating_pattern and reasoning_pattern:
                rating = float(rating_pattern.group(1))
                reasoning = reasoning_pattern.group(1)
                return min(max(rating, 0), 10), reasoning
            return 0, "Failed to parse AI response"
            
        # Process all tool calls
        ratings_with_reasonings = []
        
        for tool_call in completion.choices[0].message.tool_calls:
            if tool_call.function.name == "rate_car":
                try:
                    # Parse the arguments from the tool call
                    args = eval(tool_call.function.arguments)
                    rating = float(args["rating"])
                    reasoning = args["reasoning"]
                    
                    # Ensure rating is within bounds
                    rating = min(max(rating, 0), 10)
                    ratings_with_reasonings.append((rating, reasoning))
                except (KeyError, ValueError, SyntaxError) as e:
                    print(f"Error parsing tool call arguments: {e}")
                    continue
        
        if not ratings_with_reasonings:
            return 0, "No valid ratings were provided"
            
        # Sort by rating to find highest and lowest
        ratings_with_reasonings.sort(key=lambda x: x[0])
        
        # Calculate average rating using all ratings
        avg_rating = round(sum(r[0] for r in ratings_with_reasonings) / len(ratings_with_reasonings), 2)
        
        # Get highest and lowest rated reasonings
        lowest_rated = f"Rated: {ratings_with_reasonings[0][0]}/10: {ratings_with_reasonings[0][1]}"
        highest_rated = f"Rated: {ratings_with_reasonings[-1][0]}/10: {ratings_with_reasonings[-1][1]}"
        
        print(f"Received {len(ratings_with_reasonings)} ratings, averaging to {avg_rating:.2f}")
        return avg_rating, lowest_rated, highest_rated
            
    except Exception as e:
        print(f"Error getting rating: {e}")
        return 0, f"Error: {str(e)}"
