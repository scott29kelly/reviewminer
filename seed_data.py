"""
Seed script for ReviewMiner - Roofing/Siding/Storm Damage Industry Mock Data

Run this to populate the database with realistic sample data for testing.
Usage: python seed_data.py
"""

import sqlite3
from datetime import datetime, timedelta
import random
from pathlib import Path

# Database path
DB_PATH = Path("data/review_miner.db")

# Ensure data directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Sample reviews - realistic homeowner complaints about roofing contractors
REVIEWS = [
    # Reddit - r/roofing discussions
    {
        "source": "reddit",
        "source_url": "https://reddit.com/r/roofing/comments/abc123",
        "product_title": "r/roofing",
        "author": "storm_damage_2024",
        "rating": None,
        "review_text": "Just had a contractor come out after the hail storm last week. He quoted me $18,000 for a full roof replacement but my insurance only approved $12,000. Now he's saying I need to pay the difference out of pocket or he won't do the work. Is this normal? I feel like I'm being squeezed here.",
        "review_date": "2025-01-15",
    },
    {
        "source": "reddit",
        "source_url": "https://reddit.com/r/roofing/comments/def456",
        "product_title": "r/roofing",
        "author": "frustrated_homeowner",
        "rating": None,
        "review_text": "Three weeks since they 'finished' my roof and I already have a leak in the master bedroom. Called them 5 times, left messages, nothing. They cashed my insurance check and disappeared. How do I even report these people?",
        "review_date": "2025-01-10",
    },
    {
        "source": "reddit",
        "source_url": "https://reddit.com/r/homeowners/comments/ghi789",
        "product_title": "r/homeowners",
        "author": "texas_homeowner",
        "rating": None,
        "review_text": "Storm chasers are out in full force after the tornado. Had 4 different guys knock on my door today. One guy was super pushy and wouldn't leave until I threatened to call the police. How do you find legitimate contractors in this mess?",
        "review_date": "2025-01-08",
    },
    {
        "source": "reddit",
        "source_url": "https://reddit.com/r/insurance/comments/jkl012",
        "product_title": "r/insurance",
        "author": "claim_nightmare",
        "rating": None,
        "review_text": "My contractor submitted the claim wrong and now insurance is denying the whole thing. He put down 'wear and tear' when it was clearly hail damage. Now I'm stuck with a $15,000 bill and the contractor says it's not his problem. I'm so stressed I can't sleep.",
        "review_date": "2025-01-05",
    },
    {
        "source": "reddit",
        "source_url": "https://reddit.com/r/roofing/comments/mno345",
        "product_title": "r/roofing",
        "author": "siding_question_guy",
        "rating": None,
        "review_text": "Got quotes from 3 different companies for vinyl siding replacement after wind damage. Prices ranged from $8,000 to $22,000 for the same job. How is there such a huge difference? Makes me feel like someone is trying to rip me off.",
        "review_date": "2025-01-03",
    },
    {
        "source": "reddit",
        "source_url": "https://reddit.com/r/roofing/comments/pqr678",
        "product_title": "r/roofing",
        "author": "newbie_homeowner_23",
        "rating": None,
        "review_text": "Contractor said he'd start Monday. It's now Thursday of the following week and no one has shown up. When I call, he says 'weather delays' but it's been sunny all week. My tarps are starting to tear and rain is in the forecast.",
        "review_date": "2024-12-28",
    },
    {
        "source": "reddit",
        "source_url": "https://reddit.com/r/homeimprovement/comments/stu901",
        "product_title": "r/homeimprovement",
        "author": "elderly_mom_help",
        "rating": None,
        "review_text": "My 78 year old mother was pressured into signing a contract after the storm. They told her she HAD to decide today or lose her insurance coverage. She signed and now wants out. The contract has a 3-day cancellation but they already removed her old shingles. What are her options?",
        "review_date": "2024-12-22",
    },
    {
        "source": "reddit",
        "source_url": "https://reddit.com/r/roofing/comments/vwx234",
        "product_title": "r/roofing",
        "author": "quality_concerned",
        "rating": None,
        "review_text": "Watched the crew installing my new roof. They were rushing, not putting in enough nails, and I swear I saw them drinking on their lunch break. When I mentioned my concerns to the foreman he got defensive and said 'we've been doing this for 20 years.' Should I stop the job?",
        "review_date": "2024-12-18",
    },
    {
        "source": "reddit",
        "source_url": "https://reddit.com/r/roofing/comments/yza567",
        "product_title": "r/roofing",
        "author": "insurance_battle",
        "rating": None,
        "review_text": "Insurance adjuster and my contractor are saying completely different things. Adjuster says it's a $7,000 repair, contractor says full replacement at $19,000. I don't know who to believe. Contractor wants me to pay upfront and 'fight the insurance later.' That sounds sketchy to me.",
        "review_date": "2024-12-15",
    },
    {
        "source": "reddit",
        "source_url": "https://reddit.com/r/legaladvice/comments/bcd890",
        "product_title": "r/legaladvice",
        "author": "contract_issues",
        "rating": None,
        "review_text": "Signed a contract for $14,000 roof replacement. After they started, they 'discovered' rotted decking and now want an additional $6,000. This wasn't in the original contract. They're holding my roof hostage basically - it's half torn off and they won't continue without the extra money.",
        "review_date": "2024-12-10",
    },
    # Google Reviews - various roofing companies
    {
        "source": "google",
        "source_url": "https://google.com/maps/reviews/abc123",
        "product_title": "Premier Storm Restoration",
        "author": "John M.",
        "rating": 1,
        "review_text": "AVOID AT ALL COSTS. They promised to start within 2 weeks of signing. It took 2 MONTHS. No communication, couldn't reach anyone. When they finally showed up, the crew was different than who came to give the estimate. They left trash all over my yard and damaged my gutters. Had to chase them for 3 weeks to get someone out to fix their mess.",
        "review_date": "2025-01-12",
    },
    {
        "source": "google",
        "source_url": "https://google.com/maps/reviews/def456",
        "product_title": "Apex Roofing Solutions",
        "author": "Sarah T.",
        "rating": 2,
        "review_text": "The sales guy was super nice but after I signed, total ghost mode. The work itself was okay but getting any updates was like pulling teeth. They cashed my check immediately but took 6 weeks to even order materials. When I asked about delays they blamed the manufacturer, then blamed weather, then blamed their schedule. Pick one.",
        "review_date": "2025-01-08",
    },
    {
        "source": "google",
        "source_url": "https://google.com/maps/reviews/ghi789",
        "product_title": "StormGuard Contractors",
        "author": "Mike R.",
        "rating": 1,
        "review_text": "They supplemented my insurance claim saying they found more damage. Insurance paid out an extra $4,000. Then they pocketed it and did the bare minimum work. When I complained they showed me the 'fine print' in the contract saying any supplemental funds go to them. Feel completely scammed. Warning to everyone: READ EVERY LINE.",
        "review_date": "2025-01-05",
    },
    {
        "source": "google",
        "source_url": "https://google.com/maps/reviews/jkl012",
        "product_title": "Reliable Roof & Siding",
        "author": "Jennifer K.",
        "rating": 2,
        "review_text": "Mixed feelings. The actual roof looks good BUT they cracked 3 of my solar panels during installation and initially denied responsibility. Took weeks of arguing and threatening legal action before they agreed to replace them. The lack of accountability is concerning even if the end product is decent.",
        "review_date": "2024-12-30",
    },
    {
        "source": "google",
        "source_url": "https://google.com/maps/reviews/mno345",
        "product_title": "Summit Exteriors LLC",
        "author": "David W.",
        "rating": 1,
        "review_text": "Where do I start? They used different shingles than what we agreed on (cheaper brand), left nails all over my driveway that punctured my tire, and the ridge vent they installed is already coming loose after one wind storm. Zero quality control. Manager was rude when I complained and basically told me to deal with it.",
        "review_date": "2024-12-25",
    },
    {
        "source": "google",
        "source_url": "https://google.com/maps/reviews/pqr678",
        "product_title": "Peak Performance Roofing",
        "author": "Lisa H.",
        "rating": 3,
        "review_text": "Work quality was fine, price was competitive. Losing stars because of the insurance headache. They told me they'd handle everything with insurance but then I got a bill for $3,500 in 'uncovered work' that was never explained to me before they started. Communication about costs was terrible.",
        "review_date": "2024-12-20",
    },
    {
        "source": "google",
        "source_url": "https://google.com/maps/reviews/stu901",
        "product_title": "American Storm Services",
        "author": "Robert J.",
        "rating": 1,
        "review_text": "Complete nightmare. They damaged my landscaping, left the job half done for a week while they worked on 'other projects,' and the final bill was $2,800 more than the estimate with no explanation. When I disputed it they threatened a mechanics lien on my house. I felt extorted into paying.",
        "review_date": "2024-12-15",
    },
    {
        "source": "google",
        "source_url": "https://google.com/maps/reviews/vwx234",
        "product_title": "Guardian Roofing Group",
        "author": "Patricia N.",
        "rating": 2,
        "review_text": "The siding work was acceptable but the experience was not. Took forever to get an estimate, then they tried to upsell me constantly. When I said no to the extras, suddenly their timeline for my job kept getting pushed back. Felt like punishment for not spending more. Unprofessional.",
        "review_date": "2024-12-10",
    },
    {
        "source": "google",
        "source_url": "https://google.com/maps/reviews/yza567",
        "product_title": "Heartland Home Exteriors",
        "author": "Thomas B.",
        "rating": 1,
        "review_text": "Save yourself the stress. Scheduled inspection - they no-showed twice. Signed contract - they lost the paperwork. Started work - wrong color shingles. Fixed that - left a gaping hole during a rainstorm. My ceiling now has water damage they refuse to cover. Currently in arbitration. Worst home improvement experience of my life.",
        "review_date": "2024-12-05",
    },
    {
        "source": "google",
        "source_url": "https://google.com/maps/reviews/bcd890",
        "product_title": "Elite Exteriors Inc",
        "author": "Amanda C.",
        "rating": 2,
        "review_text": "The crew seemed inexperienced. I noticed improper flashing around my chimney which will definitely cause leaks down the road. When I pointed it out, they said it was 'good enough.' Had to escalate to the owner who finally sent someone to redo it properly. Shouldn't have to fight for quality.",
        "review_date": "2024-11-28",
    },
    # Yelp Reviews
    {
        "source": "yelp",
        "source_url": "https://yelp.com/biz/abc123",
        "product_title": "Midwest Storm Repair",
        "author": "Chris L.",
        "rating": 1,
        "review_text": "BUYER BEWARE! They told me I needed a complete roof replacement after hail damage. Got a second opinion - just needed minor repairs, less than $800. They were trying to charge me $17,000 for unnecessary work. How many people have they ripped off who didn't bother to verify?",
        "review_date": "2025-01-10",
    },
    {
        "source": "yelp",
        "source_url": "https://yelp.com/biz/def456",
        "product_title": "All-Weather Roofing",
        "author": "Nancy D.",
        "rating": 2,
        "review_text": "The work was done eventually but the constant excuses were exhausting. First it was supply chain issues, then crew scheduling, then weather. I understand things happen but a 3-week job turned into 3 months. Meanwhile I was paying to store my patio furniture because they were using my backyard as a staging area.",
        "review_date": "2025-01-05",
    },
    {
        "source": "yelp",
        "source_url": "https://yelp.com/biz/ghi789",
        "product_title": "Pro Roof Systems",
        "author": "Kevin F.",
        "rating": 1,
        "review_text": "The hidden fees, oh my god the hidden fees. Permit fee - not included. Disposal fee - not included. Insurance claim processing fee - not included. Started at $14,000, ended at $18,500. I feel completely taken advantage of. They know homeowners are vulnerable after storm damage and they exploit it.",
        "review_date": "2024-12-28",
    },
    {
        "source": "yelp",
        "source_url": "https://yelp.com/biz/jkl012",
        "product_title": "First Choice Exteriors",
        "author": "Margaret W.",
        "rating": 2,
        "review_text": "Communication was the biggest issue. Different people telling me different things. The salesman said one timeline, the scheduler said another, the foreman said something else. Nobody seemed to know what was happening. I literally had to manage the project myself to get it done.",
        "review_date": "2024-12-22",
    },
    {
        "source": "yelp",
        "source_url": "https://yelp.com/biz/mno345",
        "product_title": "StormPro Solutions",
        "author": "Steve G.",
        "rating": 1,
        "review_text": "Used them for siding after wind damage. They measured wrong and ordered the wrong amount of material. Rather than admitting their mistake, they tried to charge me for 'additional material' to finish the job. When I refused, they left one side of my house unfinished for a month. Unbelievable.",
        "review_date": "2024-12-18",
    },
    {
        "source": "yelp",
        "source_url": "https://yelp.com/biz/pqr678",
        "product_title": "Hometown Roofing Co",
        "author": "Diana R.",
        "rating": 2,
        "review_text": "They subbed out the work to a crew that barely spoke English. Not a language issue - a quality issue. The homeowner next door who watched them said they were cutting every corner possible. Now 6 months later I have loose shingles and the warranty claim is being denied.",
        "review_date": "2024-12-12",
    },
    {
        "source": "yelp",
        "source_url": "https://yelp.com/biz/stu901",
        "product_title": "Legacy Storm Restoration",
        "author": "Brian M.",
        "rating": 1,
        "review_text": "They broke my attic fan during the roof replacement and tried to hide it. Only noticed because my attic was 120 degrees in summer. When I confronted them with photos showing it was working before, they finally admitted fault but took 2 months to send someone to fix it. No accountability.",
        "review_date": "2024-12-05",
    },
    {
        "source": "yelp",
        "source_url": "https://yelp.com/biz/vwx234",
        "product_title": "Prime Exteriors Group",
        "author": "Carolyn S.",
        "rating": 1,
        "review_text": "High pressure sales tactics from start to finish. They wouldn't give me a written estimate unless I signed a 'non-binding intent form' first. Surprise - it was actually binding! Had to get a lawyer involved to get out of the contract. Cost me $800 in legal fees. Avoid!",
        "review_date": "2024-11-28",
    },
    {
        "source": "yelp",
        "source_url": "https://yelp.com/biz/yza567",
        "product_title": "Superior Storm Solutions",
        "author": "Edward T.",
        "rating": 2,
        "review_text": "The actual roof is fine but the process was hell. They scheduled and rescheduled 4 times. Each time I had to take off work to be home. Lost 4 vacation days waiting for crews that didn't show. No compensation offered, not even an apology. My time apparently means nothing to them.",
        "review_date": "2024-11-20",
    },
    {
        "source": "yelp",
        "source_url": "https://yelp.com/biz/bcd890",
        "product_title": "Action Roofing & Siding",
        "author": "Helen P.",
        "rating": 1,
        "review_text": "I'm a single woman and felt completely taken advantage of. They quoted me 40% higher than what my male neighbor got for the same work from the same company. When I confronted them with his quote they suddenly found 'discounts' they could apply. Discriminatory pricing is disgusting.",
        "review_date": "2024-11-15",
    },
    # BBB Complaints
    {
        "source": "bbb",
        "source_url": "https://bbb.org/complaint/abc123",
        "product_title": "National Storm Restoration",
        "author": "James H.",
        "rating": 1,
        "review_text": "Filed claim after they abandoned job mid-project. They collected 60% deposit ($9,600) and never returned. Phone disconnected. Office empty. Now I have a half-finished roof and no recourse. They're not even licensed in my state as it turns out. Do your research!",
        "review_date": "2025-01-08",
    },
    {
        "source": "bbb",
        "source_url": "https://bbb.org/complaint/def456",
        "product_title": "Certified Storm Experts",
        "author": "Marie K.",
        "rating": 1,
        "review_text": "Their 'lifetime warranty' is worthless. Company changed names after a year and claims no responsibility for previous work. Same owner, same office, same crew - different LLC name. Classic warranty dodge. Now my warranty claim is denied and I'm out $16,000 for a roof that's already failing.",
        "review_date": "2024-12-30",
    },
    {
        "source": "bbb",
        "source_url": "https://bbb.org/complaint/ghi789",
        "product_title": "American Exterior Pros",
        "author": "William D.",
        "rating": 1,
        "review_text": "They forged my signature on the insurance assignment form. I never signed anything giving them rights to deal directly with my insurance. Then they filed a claim without my knowledge and cashed the check that came to my address while I was out of town. Currently pursuing criminal charges.",
        "review_date": "2024-12-20",
    },
    {
        "source": "bbb",
        "source_url": "https://bbb.org/complaint/jkl012",
        "product_title": "Quality Storm Services",
        "author": "Ruth A.",
        "rating": 1,
        "review_text": "They put a lien on my house for 'unpaid balance' that I never agreed to. The original contract was $12,000 which I paid in full. They're claiming $18,000 due to 'scope changes' that were never discussed with me or documented. I'm being forced to pay to clear the lien so I can refinance. Extortion.",
        "review_date": "2024-12-10",
    },
    {
        "source": "bbb",
        "source_url": "https://bbb.org/complaint/mno345",
        "product_title": "Trusted Home Exteriors",
        "author": "Charles E.",
        "rating": 1,
        "review_text": "Worst customer service imaginable. After the job was 'complete' I found they hadn't replaced damaged plywood under the shingles - just covered over the rot. Inspector caught it during home sale. Company refused to fix, said inspection was 'beyond scope.' Cost me the sale. House still not sold.",
        "review_date": "2024-11-30",
    },
    # More Reddit posts
    {
        "source": "reddit",
        "source_url": "https://reddit.com/r/roofing/comments/efg123",
        "product_title": "r/roofing",
        "author": "hailstorm_survivor",
        "rating": None,
        "review_text": "Anyone else notice contractors jacking up prices right after a big storm? Before the hail, I was quoted $9,000 for my roof. After the hail, suddenly the same job is $16,000 because of 'demand.' Same house, same roof, same materials. Just gouging people when they're desperate.",
        "review_date": "2024-11-25",
    },
    {
        "source": "reddit",
        "source_url": "https://reddit.com/r/insurance/comments/hij456",
        "product_title": "r/insurance",
        "author": "fighting_my_claim",
        "rating": None,
        "review_text": "My insurance only covered ACV (actual cash value) not RCV (replacement cost). The roofer knew this but told me to 'just pay and we'll figure it out.' Now I owe $6,000 out of pocket because he didn't explain the insurance process properly. I feel misled.",
        "review_date": "2024-11-22",
    },
    {
        "source": "reddit",
        "source_url": "https://reddit.com/r/homeowners/comments/klm789",
        "product_title": "r/homeowners",
        "author": "siding_problems",
        "rating": None,
        "review_text": "Got siding replaced after storm damage. The color match is terrible - new siding is clearly a different shade than what wasn't damaged. Company says that's normal due to 'sun fading' on old siding but it's been less than a year since original install. They won't redo it.",
        "review_date": "2024-11-18",
    },
    {
        "source": "reddit",
        "source_url": "https://reddit.com/r/roofing/comments/nop012",
        "product_title": "r/roofing",
        "author": "gutters_and_more",
        "rating": None,
        "review_text": "They said gutter replacement was 'included' in the roof job. After work was done, they sent a separate bill for gutters saying 'included' meant included in the scope, not the price. $2,100 I wasn't expecting. Everything with these people is a gotcha.",
        "review_date": "2024-11-15",
    },
    {
        "source": "reddit",
        "source_url": "https://reddit.com/r/legaladvice/comments/qrs345",
        "product_title": "r/legaladvice",
        "author": "roofing_legal_help",
        "rating": None,
        "review_text": "Contractor is threatening to sue me because I left a negative review. He's claiming defamation but everything I wrote was 100% true and documented with photos. Can he actually do this? I just wanted to warn other homeowners about my experience.",
        "review_date": "2024-11-10",
    },
    {
        "source": "reddit",
        "source_url": "https://reddit.com/r/roofing/comments/tuv678",
        "product_title": "r/roofing",
        "author": "inspection_issues",
        "rating": None,
        "review_text": "City inspector failed my roof installation because the contractor didn't use the right underlayment for my climate zone. Now the contractor is blaming ME for not telling him what zone I'm in. How would I know? Isn't that literally his job?",
        "review_date": "2024-11-05",
    },
    {
        "source": "reddit",
        "source_url": "https://reddit.com/r/homeimprovement/comments/wxy901",
        "product_title": "r/homeimprovement",
        "author": "DIY_regret",
        "rating": None,
        "review_text": "Paid a contractor to fix storm damage because I didn't trust myself to do it right. Turned out I could have done a better job watching YouTube videos. The flashing is crooked, the drip edge is bent, and there are visible gaps. I'm honestly embarrassed for them.",
        "review_date": "2024-11-01",
    },
    # More Google Reviews
    {
        "source": "google",
        "source_url": "https://google.com/maps/reviews/efg012",
        "product_title": "Thunder Roofing Co",
        "author": "Sandra M.",
        "rating": 1,
        "review_text": "The salesman claimed they were a 'local family company' but they're actually a franchise from out of state. The corporate office is impossible to reach and the local manager has no authority to resolve issues. Completely misleading advertising. I wanted to support local business and got duped.",
        "review_date": "2024-10-28",
    },
    {
        "source": "google",
        "source_url": "https://google.com/maps/reviews/hij345",
        "product_title": "Titan Exteriors",
        "author": "George R.",
        "rating": 2,
        "review_text": "They were supposed to clean up after themselves each day per the contract. Instead they left piles of old shingles, nails, and debris in my yard for the entire week. My dog stepped on a nail. Vet bill was $400. They refused to reimburse saying 'that's what the magnetic sweeper is for' but they never used one.",
        "review_date": "2024-10-22",
    },
    {
        "source": "google",
        "source_url": "https://google.com/maps/reviews/klm678",
        "product_title": "Metro Storm Repair",
        "author": "Donna K.",
        "rating": 1,
        "review_text": "They sent a crew at 6:30 AM without any notice. Woke up the whole neighborhood with banging and an industrial dumpster being dropped in my driveway. When I complained they said they have 'the right' to start at any time. No consideration for others. Even if the work was perfect (it wasn't) this alone loses all my stars.",
        "review_date": "2024-10-18",
    },
    {
        "source": "google",
        "source_url": "https://google.com/maps/reviews/nop901",
        "product_title": "Cornerstone Roofing",
        "author": "Paul V.",
        "rating": 1,
        "review_text": "Insurance fraud. They inflated the damage report to get a bigger payout, then pocketed the difference. When I realized what happened (my premium went up significantly), they wouldn't return my calls. Now I look like a fraud participant even though I had no idea.",
        "review_date": "2024-10-12",
    },
    {
        "source": "google",
        "source_url": "https://google.com/maps/reviews/qrs234",
        "product_title": "Horizon Home Services",
        "author": "Betty L.",
        "rating": 2,
        "review_text": "The project manager changed 3 times during my siding job. Each new PM had no idea what the previous one promised. I had to explain my project from scratch every time. How hard is it to keep notes? This is basic customer service. The only reason they get 2 stars is the actual work looks okay.",
        "review_date": "2024-10-05",
    },
    # More Yelp Reviews
    {
        "source": "yelp",
        "source_url": "https://yelp.com/biz/efg012",
        "product_title": "Regional Roofing Pros",
        "author": "Frank W.",
        "rating": 1,
        "review_text": "They require your insurance deductible upfront before even doing an inspection. When I asked why, they got defensive and said 'that's how insurance jobs work.' No other company required this. Felt like a red flag and I walked away. Glad I did after reading other reviews.",
        "review_date": "2024-09-30",
    },
    {
        "source": "yelp",
        "source_url": "https://yelp.com/biz/hij345",
        "product_title": "Valley Storm Experts",
        "author": "Laura H.",
        "rating": 2,
        "review_text": "The initial quote was competitive. But then 'recommended upgrades' started piling on. Better shingles, ice dam protection, improved ventilation. All 'strongly recommended.' By the time they were done upselling, the price doubled. It's exhausting when you just want a fair deal.",
        "review_date": "2024-09-25",
    },
    {
        "source": "yelp",
        "source_url": "https://yelp.com/biz/klm678",
        "product_title": "Summit Storm Services",
        "author": "Richard P.",
        "rating": 1,
        "review_text": "They took my $8,000 deposit and strung me along for 4 months with promises. 'Next week' turned into 'next month' turned into 'we're behind due to weather.' I demanded a refund and suddenly they had time the following week. Deposit hostage situation. Pathetic.",
        "review_date": "2024-09-20",
    },
    {
        "source": "yelp",
        "source_url": "https://yelp.com/biz/nop901",
        "product_title": "Premier Roof & Siding",
        "author": "Janet C.",
        "rating": 1,
        "review_text": "Asked for GAF HDZ shingles because of the warranty. They used a different brand that 'looks the same.' When I noticed and complained, they offered $500 off instead of replacing with the correct product. I wanted the warranty, not a discount on inferior materials!",
        "review_date": "2024-09-15",
    },
    {
        "source": "yelp",
        "source_url": "https://yelp.com/biz/qrs234",
        "product_title": "Rapid Restoration Inc",
        "author": "Dennis M.",
        "rating": 2,
        "review_text": "Communication is non-existent once they have your money. I had to text, call, and email just to get basic updates. The owner finally admitted they 'took on too many jobs' after the storm. I get it, business is good, but don't overbook and leave customers hanging.",
        "review_date": "2024-09-08",
    },
]

# Pain point categories for the roofing industry
PAIN_POINT_TEMPLATES = [
    # Communication Issues
    {
        "category": "Communication",
        "quotes": [
            "Called them 5 times, left messages, nothing",
            "couldn't reach anyone",
            "Complete ghost mode after I signed",
            "Getting any updates was like pulling teeth",
            "Different people telling me different things",
            "Nobody seemed to know what was happening",
            "I had to text, call, and email just to get basic updates",
            "No communication, couldn't reach anyone",
            "No notice before they started at 6:30 AM",
            "Each new PM had no idea what the previous one promised",
        ],
        "implied_needs": [
            "Regular proactive updates throughout the project",
            "A single point of contact who is responsive",
            "Clear communication channels that actually work",
            "Consistent information from all team members",
            "Written documentation of all agreements",
        ],
    },
    # Pricing Issues
    {
        "category": "Pricing",
        "quotes": [
            "quoted me $18,000 but insurance only approved $12,000",
            "Prices ranged from $8,000 to $22,000 for the same job",
            "Started at $14,000, ended at $18,500",
            "hidden fees, oh my god the hidden fees",
            "wanted an additional $6,000 after they started",
            "40% higher than what my male neighbor got",
            "jacking up prices right after a big storm",
            "final bill was $2,800 more than the estimate",
            "By the time they were done upselling, the price doubled",
            "Permit fee - not included. Disposal fee - not included",
        ],
        "implied_needs": [
            "Transparent all-inclusive pricing upfront",
            "Written estimates that don't change",
            "Fair pricing regardless of gender",
            "Protection from price gouging after disasters",
            "Clear explanation of what insurance covers",
        ],
    },
    # Quality Issues
    {
        "category": "Quality",
        "quotes": [
            "already have a leak in the master bedroom",
            "not putting in enough nails",
            "used different shingles than what we agreed on",
            "ridge vent is already coming loose",
            "improper flashing around my chimney",
            "The color match is terrible",
            "The flashing is crooked, the drip edge is bent",
            "didn't replace damaged plywood - just covered over the rot",
            "cutting every corner possible",
            "visible gaps in the work",
        ],
        "implied_needs": [
            "Quality workmanship that matches specifications",
            "Installation that passes inspection first time",
            "Materials that match what was agreed upon",
            "Work that lasts and doesn't fail quickly",
            "Attention to detail on all aspects of the job",
        ],
    },
    # Timeliness Issues
    {
        "category": "Timeliness",
        "quotes": [
            "promised to start within 2 weeks, took 2 MONTHS",
            "It's now Thursday and no one has shown up",
            "a 3-week job turned into 3 months",
            "left the job half done for a week",
            "Scheduled and rescheduled 4 times",
            "strung me along for 4 months with promises",
            "took 6 weeks to even order materials",
            "Lost 4 vacation days waiting for crews that didn't show",
            "My tarps are starting to tear and rain is in the forecast",
            "left one side of my house unfinished for a month",
        ],
        "implied_needs": [
            "Realistic timelines that are actually kept",
            "Reliable scheduling that respects homeowner's time",
            "Quick mobilization after contract signing",
            "Continuous work until project completion",
            "Protection of home during delays",
        ],
    },
    # Insurance Issues
    {
        "category": "Insurance",
        "quotes": [
            "submitted the claim wrong and now insurance is denying",
            "Insurance adjuster and contractor saying completely different things",
            "told me they'd handle everything with insurance but then I got a bill",
            "Only covered ACV not RCV and the roofer knew this",
            "inflated the damage report to get a bigger payout",
            "forged my signature on the insurance assignment form",
            "cashed my insurance check and disappeared",
            "Any supplemental funds go to them according to fine print",
            "telling her she HAD to decide today or lose insurance coverage",
            "Now my premium went up significantly",
        ],
        "implied_needs": [
            "Honest and accurate insurance claim handling",
            "Clear explanation of insurance process and coverage",
            "Contractor who works with insurance, not against it",
            "Protection from insurance fraud schemes",
            "Transparency about what homeowner will owe",
        ],
    },
    # Contractor Trustworthiness
    {
        "category": "Trustworthiness",
        "quotes": [
            "Storm chasers are out in full force",
            "They cashed my check and disappeared",
            "Feel completely scammed",
            "pressured into signing a contract",
            "wouldn't leave until I threatened to call the police",
            "High pressure sales tactics",
            "threatening to sue me because I left a negative review",
            "claimed they were a 'local family company' but they're actually a franchise",
            "Company changed names after a year",
            "Same owner, same office, same crew - different LLC name",
        ],
        "implied_needs": [
            "Verified local contractors with established reputation",
            "No-pressure sales environment",
            "Companies that stand behind their work long-term",
            "Protection from predatory storm chasers",
            "Honest representation of company identity",
        ],
    },
    # Accountability Issues
    {
        "category": "Accountability",
        "quotes": [
            "When I complained they showed me the 'fine print'",
            "refused responsibility",
            "said it was 'good enough'",
            "Manager was rude when I complained",
            "took 2 months to send someone to fix it",
            "Shouldn't have to fight for quality",
            "Zero quality control",
            "threatening a mechanics lien on my house",
            "tried to hide it",
            "blaming ME for not telling him what zone I'm in",
        ],
        "implied_needs": [
            "Contractors who own their mistakes",
            "Quick resolution of problems",
            "Fair and clear contracts without hidden clauses",
            "Respectful treatment when issues arise",
            "Proper documentation and quality checks",
        ],
    },
    # Professionalism Issues
    {
        "category": "Professionalism",
        "quotes": [
            "I swear I saw them drinking on their lunch break",
            "left trash all over my yard",
            "damaged my landscaping",
            "cracked 3 of my solar panels",
            "nails all over my driveway that punctured my tire",
            "Woke up the whole neighborhood at 6:30 AM",
            "My dog stepped on a nail",
            "left piles of old shingles and debris in my yard",
            "broke my attic fan and tried to hide it",
            "damaged my gutters",
        ],
        "implied_needs": [
            "Professional crew behavior on the job",
            "Proper cleanup and debris removal",
            "Care for existing property and landscaping",
            "Reasonable working hours with notice",
            "Full accountability for any damage caused",
        ],
    },
]

# Sample scrape jobs
SCRAPE_JOBS = [
    {
        "source": "reddit",
        "query": "roofing contractor complaints",
        "status": "completed",
        "reviews_found": 18,
        "started_at": "2025-01-15T10:30:00",
        "completed_at": "2025-01-15T10:45:00",
    },
    {
        "source": "google",
        "query": "storm damage roofing companies reviews",
        "status": "completed",
        "reviews_found": 15,
        "started_at": "2025-01-14T14:00:00",
        "completed_at": "2025-01-14T14:20:00",
    },
    {
        "source": "yelp",
        "query": "roofing siding contractors",
        "status": "completed",
        "reviews_found": 12,
        "started_at": "2025-01-13T09:15:00",
        "completed_at": "2025-01-13T09:35:00",
    },
    {
        "source": "bbb",
        "query": "roofing company complaints",
        "status": "completed",
        "reviews_found": 5,
        "started_at": "2025-01-12T16:45:00",
        "completed_at": "2025-01-12T16:55:00",
    },
    {
        "source": "reddit",
        "query": "insurance claim roofing",
        "status": "completed",
        "reviews_found": 8,
        "started_at": "2025-01-11T11:00:00",
        "completed_at": "2025-01-11T11:18:00",
    },
    {
        "source": "google",
        "query": "hail damage roof repair reviews",
        "status": "completed",
        "reviews_found": 10,
        "started_at": "2025-01-10T13:30:00",
        "completed_at": "2025-01-10T13:50:00",
    },
]


def seed_database():
    """Seed the database with mock data."""
    print("[SEED] Seeding ReviewMiner database with roofing industry data...\n")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_url TEXT,
            product_title TEXT,
            product_url TEXT,
            author TEXT,
            rating INTEGER,
            review_text TEXT NOT NULL,
            review_date TEXT,
            scraped_at TEXT DEFAULT CURRENT_TIMESTAMP,
            processed BOOLEAN DEFAULT FALSE,
            UNIQUE(source, source_url, review_text)
        );

        CREATE TABLE IF NOT EXISTS pain_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            verbatim_quote TEXT NOT NULL,
            emotional_intensity TEXT,
            implied_need TEXT,
            extracted_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (review_id) REFERENCES reviews(id)
        );

        CREATE TABLE IF NOT EXISTS scrape_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            query TEXT,
            status TEXT DEFAULT 'pending',
            reviews_found INTEGER DEFAULT 0,
            started_at TEXT,
            completed_at TEXT,
            error_message TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_reviews_source ON reviews(source);
        CREATE INDEX IF NOT EXISTS idx_reviews_processed ON reviews(processed);
        CREATE INDEX IF NOT EXISTS idx_pain_points_category ON pain_points(category);
    """)
    
    # Clear existing data
    cursor.execute("DELETE FROM pain_points")
    cursor.execute("DELETE FROM reviews")
    cursor.execute("DELETE FROM scrape_jobs")
    conn.commit()
    print("[OK] Cleared existing data")
    
    # Insert reviews
    review_count = 0
    for review in REVIEWS:
        cursor.execute(
            """
            INSERT INTO reviews (source, source_url, product_title, product_url, author, rating, review_text, review_date, processed, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review["source"],
                review["source_url"],
                review["product_title"],
                None,  # product_url
                review["author"],
                review["rating"],
                review["review_text"],
                review["review_date"],
                True,  # processed
                datetime.now().isoformat(),
            ),
        )
        review_count += 1
    
    conn.commit()
    print(f"[OK] Inserted {review_count} reviews")
    
    # Get review IDs for pain point assignment
    cursor.execute("SELECT id FROM reviews")
    review_ids = [row[0] for row in cursor.fetchall()]
    
    # Insert pain points
    pain_point_count = 0
    intensities = ["low", "medium", "high"]
    
    for template in PAIN_POINT_TEMPLATES:
        category = template["category"]
        quotes = template["quotes"]
        needs = template["implied_needs"]
        
        for quote in quotes:
            # Assign to a random review
            review_id = random.choice(review_ids)
            intensity = random.choice(intensities)
            implied_need = random.choice(needs)
            
            cursor.execute(
                """
                INSERT INTO pain_points (review_id, category, verbatim_quote, emotional_intensity, implied_need, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    review_id,
                    category,
                    quote,
                    intensity,
                    implied_need,
                    datetime.now().isoformat(),
                ),
            )
            pain_point_count += 1
    
    conn.commit()
    print(f"[OK] Inserted {pain_point_count} pain points")
    
    # Insert scrape jobs
    job_count = 0
    for job in SCRAPE_JOBS:
        cursor.execute(
            """
            INSERT INTO scrape_jobs (source, query, status, reviews_found, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                job["source"],
                job["query"],
                job["status"],
                job["reviews_found"],
                job["started_at"],
                job["completed_at"],
            ),
        )
        job_count += 1
    
    conn.commit()
    print(f"[OK] Inserted {job_count} scrape jobs")
    
    conn.close()
    
    # Print summary
    print("\n" + "=" * 50)
    print("Seed Data Summary")
    print("=" * 50)
    print(f"  Reviews:     {review_count}")
    print(f"  Pain Points: {pain_point_count}")
    print(f"  Scrape Jobs: {job_count}")
    print("=" * 50)
    
    # Print category breakdown
    print("\nPain Points by Category:")
    for template in PAIN_POINT_TEMPLATES:
        count = len(template["quotes"])
        print(f"  - {template['category']}: {count}")
    
    # Print source breakdown
    print("\nReviews by Source:")
    source_counts = {}
    for review in REVIEWS:
        source = review["source"]
        source_counts[source] = source_counts.get(source, 0) + 1
    for source, count in sorted(source_counts.items()):
        print(f"  - {source}: {count}")
    
    print("\n[SUCCESS] Database seeded successfully!")
    print(f"Database location: {DB_PATH.absolute()}")


if __name__ == "__main__":
    seed_database()
