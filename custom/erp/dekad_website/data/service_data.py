# -*- coding: utf-8 -*-
from .translate_utils import _lt

SERVICES_CATALOG = {
    'odoo-consultancy': {
        'hero_title': _lt('Build Smarter, Operate Better'),
        'hero_desc': _lt("We help organizations rethink, restructure, and optimize their operations using proven strategies and ERP-driven insights. Whether you're launching a new process, improving an existing one, or planning full digital transformation—our consultants work as part of your team to get it done."),
        'hero_bg_image': '/dekad_website/static/src/img/migrated/services/odoo-consultancy/hero_bg_image.png',
        'timeline_title': _lt('Consultancy Process'),
        'timeline_subtitle': _lt('Laying the foundation for a successful ERP journey'),
        'timeline_steps': [
            {'title': _lt('Initial Consultation'),
             'desc': _lt('We meet with your team to understand your business model, challenges, and goals.')},
            {'title': _lt('Process Mapping'),
             'desc': _lt('We analyze your existing workflows and identify inefficiencies or gaps.')},
            {'title': _lt('Solution Recommendation'),
             'desc': _lt('Based on your needs, we recommend the right modules, structure, and scope of the ERP system.')},
            {'title': _lt('Feasibility & Gap Analysis'),
             'desc': _lt('We compare your requirements with available features and identify what needs customization.')},
            {'title': _lt('Project Planning'),
             'desc': _lt('We define the roadmap—timelines, responsibilities, priorities, and measurable outcomes—to guide the implementation phase.')}
        ]
    },
    'odoo-implementation': {
        'hero_title': _lt('Seamless ERP Implementation'),
        'hero_desc': _lt("We don’t just install software—we deliver operational transformation. Our implementation services ensure that your ERP system is configured to mirror your processes, ready to support your team, and able to scale as you grow."),
        'hero_bg_image': '/dekad_website/static/src/img/migrated/services/odoo-implementation/hero_bg_image.webp',
        'timeline_title': _lt('Process Line'),
        'timeline_subtitle': _lt('Step-by-step. Clear. Proven.'),
        'timeline_steps': [
            {'title': _lt('Blueprint & Kickoff'),
             'desc': _lt('We start with interactive workshops to map your specific workflows and goals. From this session, we craft a clear project roadmap—including features, responsibilities, and timelines—to ensure full transparency and alignment.')},
            {'title': _lt('System Configuration'),
             'desc': _lt('Our team configures core modules—finance, sales, inventory, and beyond—tailored to your business rules. Supported by expert data migration strategies, we ensure a clean, accurate transition from old systems with zero operational disruption.')},
            {'title': _lt('Customization & Extensions'),
             'desc': _lt('We follow a clear 8-step customization process—from gathering your requirements and analyzing gaps, to feasibility checks, cost estimation, development, testing, and final delivery—ensuring each solution fits your exact business needs.')},
            {'title': _lt('Testing & UAT'),
             'desc': _lt('Before going live, we guide you through user-acceptance testing to validate every workflow. Then we conduct hands-on training sessions—online or onsite—equipping your staff with the skills and documentation needed for confident day-one use.')},
            {'title': _lt('Training & Onboarding'),
             'desc': _lt('We train your users through interactive sessions and documentation. By go-live, your team is confident and ready to use the system efficiently.')},
            {'title': _lt('Go-Live & Post-Launch Support'),
             'desc': _lt('We’re with you at go-live, ready to address any issues in real time. After launch, our local support team monitors performance, stabilizes processes, provides refresher training, and helps you continuously improve.')}
        ]
    },
    'odoo-integration': {
        'hero_title': _lt('Unified System Integration'),
        'hero_desc': _lt('Our Integration service ensures your ERP becomes the central hub of your business—efficiently connected to your website, CRM, external systems, payment gateways, and more. Eliminate data silos, automate information flow, and enhance user experience across all platforms.'),
        'hero_bg_image': '/dekad_website/static/src/img/migrated/services/odoo-integration/hero_bg_image.webp',
        'timeline_title': _lt('Integration Process'),
        'timeline_subtitle': _lt('Connecting every system to work as one'),
        'timeline_steps': [
            {
                'title': _lt('Centralized Business Operations'),
                'desc': _lt('Unify your scattered systems into one seamless workflow. We integrate your POS, eCommerce, CRM, HR, accounting, and third-party tools into a single, efficient platform.')
            },
            {
                'title': _lt('API & Third-Party Integration'),
                'desc': _lt('From payment gateways and shipping providers to custom APIs—we ensure your tools talk to each other, reducing manual work and boosting productivity.')
            },
            {
                'title': _lt('Real-Time Data Sync'),
                'desc': _lt('Say goodbye to data silos. We enable real-time syncing across platforms, giving you up-to-date insights and enabling faster, smarter decisions.')
            },
            {
                'title': _lt('Secure & Scalable Architecture'),
                'desc': _lt("Our integrations are built to last—robust, secure, and designed to grow with your business. Whether it's cloud, on-premise, or hybrid, we tailor it to your infrastructure.")
            }
        ]
    },
    'odoo-support': {
        'hero_title': _lt('24/7 Dedicated Support'),
        'hero_desc': _lt("Benefit from round-the-clock assistance to keep your ERP system operating smoothly. Whether it's urgent issue resolution, general enquiries, or strategic system queries—our local support team is ready to help, day or night."),
        'hero_bg_image': '/dekad_website/static/src/img/migrated/services/odoo-support/hero_bg_image.jpg',
        'timeline_title': _lt('Support Process'),
        'timeline_subtitle': _lt('Reliable help, whenever you need it'),
        'timeline_steps': [
            {
                'title': _lt('Issue Diagnosis & Prioritization'),
                'desc': _lt('We identify the root cause of issues quickly and classify them by urgency—ensuring critical operations are never left hanging.')
            },
            {
                'title': _lt('Expert Resolution'),
                'desc': _lt('Our functional and technical experts work hand-in-hand to resolve bugs, data errors, and configuration challenges—fast and efficiently.')
            },
            {
                'title': _lt('Performance Monitoring'),
                'desc': _lt('We continuously track your system’s health and recommend optimizations before issues arise—so your business stays one step ahead.')
            },
            {
                'title': _lt('User Guidance & Training'),
                'desc': _lt('From answering your team’s daily questions to walking them through system updates, we’re here to ensure confident, capable usage.')
            }
        ]
    },
    'odoo-migration': {
        'hero_title': _lt('Effortless Data Migration'),
        'hero_desc': _lt('Our Data Migration service ensures a seamless transfer of your crucial business data—clients, inventory, transactions, accounting, and more—from legacy systems or spreadsheets into your new ERP. We preserve history, minimize downtime, and validate everything to guarantee a smooth transition.'),
        'hero_bg_image': '/dekad_website/static/src/img/migrated/services/odoo-migration/hero_bg_image.jpg',
        'timeline_title': _lt('Migration Process'),
        'timeline_subtitle': _lt('Seamless upgrades without disruption'),
        'timeline_steps': [
            {
                'title': _lt('System Audit & Preparation'),
                'desc': _lt('We evaluate your current setup to understand customizations, data volume, and compatibility before moving forward.')
            },
            {
                'title': _lt('Data Backup & Cleansing'),
                'desc': _lt('Your data is securely backed up, cleaned, and prepped to ensure a smooth and safe transition to the new version.')
            },
            {
                'title': _lt('Version Upgrade & Testing'),
                'desc': _lt('We upgrade your platform to the latest version, conduct thorough testing, and verify that all features and workflows function as expected.')
            },
            {
                'title': _lt('Go-Live & Support'),
                'desc': _lt('Once stable, we roll out the new version—ensuring minimal downtime and providing ongoing support to keep everything running smoothly.')
            }
        ]
    },
    'odoo-web-design': {
        'hero_title': _lt('Custom Web Design That Converts'),
        'hero_desc': _lt('We create visually appealing, responsive, and fully integrated websites using Odoo’s Website Builder. Whether you need a corporate site, online store, or landing pages, we tailor every pixel to your brand—while connecting it to your sales, CRM, inventory, and marketing systems.'),
        'hero_bg_image': '/dekad_website/static/src/img/migrated/services/odoo-web-design/hero_bg_image.jpg',
        'timeline_title': _lt('Web Design Process'),
        'timeline_subtitle': _lt('Beautiful, functional, and built to grow with your business'),
        'timeline_steps': [
            {
                'title': _lt('Tailored Website Strategy'),
                'desc': _lt('We begin with a discovery session to understand your brand, audience, and goals. From there, we define your website’s structure, user journey, and content flow—aligning design with business outcomes.')
            },
            {
                'title': _lt('Pixel-Perfect Design'),
                'desc': _lt('Our UI/UX experts craft clean, modern layouts using Odoo’s drag-and-drop builder. Everything is responsive by default and designed to look flawless on desktop, tablet, and mobile.')
            },
            {
                'title': _lt('Content Blocks & Dynamic Pages'),
                'desc': _lt('Use pre-built or custom-designed blocks to manage content easily. We set up dynamic pages (like product, blog, or service listings) that update automatically—no coding required.')
            },
            {
                'title': _lt('Multi-Language & RTL Support'),
                'desc': _lt('Need Arabic and English? We design multilingual, RTL-friendly sites that reflect your brand identity across languages and regions.')
            },
            {
                'title': _lt('Full Integration with Odoo Apps'),
                'desc': _lt('Your website connects with Odoo CRM, Sales, Inventory, Helpdesk, and eCommerce—creating a seamless flow from visitor to customer without switching tools.')
            },
            {
                'title': _lt('SEO & Performance Optimization'),
                'desc': _lt('We optimize every page for speed, SEO, and mobile usability. Built-in tools like meta tags, sitemap, and schema are all properly configured for visibility and ranking.')
            }
        ]
    }
}