import json
import re

from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template
from company_ai_project.ui.company_ui.right_widget.company_common_widget import company_common
from company_ai_project.ui.company_ui.right_widget.user_widget.right_widget.user_common_right_widget import \
    task_widget_ui

test = {
    "engagement_plan": {
        "client_name": "DESLY GROUP CO.,LTD.",
        "user_company": "Nexus Export",
        "phases": [
            {
                "phase_number": 1,
                "phase_name": "Research & Positioning",
                "duration_weeks": 2,
                "objective": "Identify specific product gaps in DESLY's portfolio where Nexus's dehydrated ingredients can add value, and craft a targeted value proposition.",
                "tasks": [
                    {
                        "task_id": "R1",
                        "task_name": "Competitive Gap Analysis",
                        "description": "Analyze DESLY's product list (Light/Dark Soy Sauce, Teriyaki, Gluten-Free sauces, Vinegar, Sesame Oil) to identify seasoning blends or dry ingredient needs. Map against Nexus's dehydrated onion, garlic, and spices (flakes, granules, powder) to find 5+ overlapping SKU opportunities for sauce bases or seasoning mixes.",
                        "owner": "Sales Head",
                        "due_by_day": 3,
                        "deliverable": "Excel matrix comparing DESLY sauces vs. Nexus dry ingredients",
                        "success_criteria": "Matrix identifies minimum 5 potential product integrations (e.g., garlic powder for teriyaki, onion granules for hoisin).",
                        "depends_on": [],
                        "status": "in_progress"
                    },
                    {
                        "task_id": "R2",
                        "task_name": "USP Benchmark",
                        "description": "Benchmark Nexus's 12-step hygienic process, 99.5% onion purity, and direct farm sourcing against typical DESLY suppliers. Highlight capability for Halal/Kosher-compliant production and advanced ozone cleaning to meet DESLY's certification standards.",
                        "owner": "Quality Manager",
                        "due_by_day": 6,
                        "deliverable": "One-page USP document",
                        "success_criteria": "Document clearly articulates 3 superior quality/safety points relevant to a sauce manufacturer.",
                        "depends_on": [
                            "R1"
                        ],
                        "status": "completed"
                    },
                    {
                        "task_id": "R3",
                        "task_name": "Private Label Opportunity Scan",
                        "description": "DESLY offers private label services. Scan for potential where Nexus's dehydrated products could be white-labeled as 'premium dry ingredient mixes' under DESLY's brand for their B2B clients or retail lines, leveraging DESLY's global distribution.",
                        "owner": "BD Strategist",
                        "due_by_day": 5,
                        "deliverable": "Opportunity brief",
                        "success_criteria": "Brief outlines 2-3 viable white-label product concepts (e.g., 'Dehydrated Allium Blend for Stir-fry Sauce').",
                        "depends_on": [],
                        "status": "blocked"
                    },
                    {
                        "task_id": "R4",
                        "task_name": "Decision-Mapper",
                        "description": "Identify key contacts at DESLY (likely Head of Procurement, R&D for new products, Private Label Manager) via LinkedIn and website. Note their GulfFood 2026 exhibition for timing relevance.",
                        "owner": "Sales Executive",
                        "due_by_day": 8,
                        "deliverable": "Organizational chart with contact hypotheses",
                        "success_criteria": "Chart identifies 3 potential decision-maker roles with rationale.",
                        "depends_on": [],
                        "status": "review"
                    },
                    {
                        "task_id": "R5",
                        "task_name": "Value Proposition Draft",
                        "description": "Synthesize R1-R4 into a core proposition: 'Nexus Export supplies high-purity, food-safe dehydrated onion, garlic & spices to enhance DESLY's sauce formulations, reduce prep time, ensure batch consistency, and support private label expansion.'",
                        "owner": "BD Strategist",
                        "due_by_day": 10,
                        "deliverable": "Final value proposition statement",
                        "success_criteria": "Statement is clear, benefit-focused, and references specific capabilities (purity, safety) and opportunities (private label).",
                        "depends_on": [
                            "R1",
                            "R2",
                            "R3"
                        ],
                        "status": "cancelled"
                    }
                ]
            },
            {
                "phase_number": 2,
                "phase_name": "Outreach & Qualification",
                "duration_weeks": 1,
                "objective": "Initiate contact with DESLY using tailored messaging and qualify their interest in dehydrated ingredients for direct sourcing.",
                "tasks": [
                    {
                        "task_id": "O1",
                        "task_name": "Draft Introductory Email",
                        "description": "Draft a concise email referencing DESLY's GulfFood participation and century-old legacy. Propose Nexus as a strategic supplier of dehydrated alliums/spices to enhance their sauce portfolio, citing purity standards (99.5% onion) and 60+ country export experience.",
                        "owner": "BD Strategist",
                        "due_by_day": 11,
                        "deliverable": "Email draft",
                        "success_criteria": "Email is personalized, references mutual B2B focus, and includes a clear call to action.",
                        "depends_on": [
                            "R5"
                        ],
                        "status": "pending"
                    },
                    {
                        "task_id": "O2",
                        "task_name": "Send Email & Follow-up",
                        "description": "Send the email to identified contacts (e.g., procurement@deslygroup.com) and schedule a follow-up call for 3 days later.",
                        "owner": "Sales Executive",
                        "due_by_day": 12,
                        "deliverable": "Email sent, follow-up scheduled",
                        "success_criteria": "Email delivered to at least 2 hypothesized contact points.",
                        "depends_on": [
                            "O1"
                        ],
                        "status": "pending"
                    },
                    {
                        "task_id": "O3",
                        "task_name": "LinkedIn Outreach",
                        "description": "Connect with mapped DESLY decision-makers on LinkedIn with a tailored note referencing the email and mutual interest in Asian sauce innovation.",
                        "owner": "Sales Head",
                        "due_by_day": 13,
                        "deliverable": "LinkedIn connection requests sent",
                        "success_criteria": "Connection requests sent to 3+ targets from R4.",
                        "depends_on": [
                            "R4"
                        ],
                        "status": "pending"
                    },
                    {
                        "task_id": "O4",
                        "task_name": "Qualification Call Script",
                        "description": "Prepare a call script to qualify DESLY's current sourcing of dry ingredients, interest in pilot SKUs (e.g., garlic powder, onion flakes), and appetite for private label collaboration. Include questions about their gluten-free line requirements.",
                        "owner": "Sales Head",
                        "due_by_day": 14,
                        "deliverable": "Structured call guide with key questions",
                        "success_criteria": "Script includes 5+ qualifying questions about volume, specs, and strategic needs.",
                        "depends_on": [
                            "R5",
                            "O2"
                        ],
                        "status": "pending"
                    }
                ]
            },
            {
                "phase_number": 3,
                "phase_name": "Proposal & Sample",
                "duration_weeks": 1,
                "objective": "Develop compelling proposal materials and trigger the evaluation process with a sample offer.",
                "tasks": [
                    {
                        "task_id": "P1",
                        "task_name": "Create 1-Pager PDF",
                        "description": "Design a one-page PDF highlighting Nexus's 15+ years experience, 12-step hygienic process, certifications alignment, and specific product recommendations for DESLY (e.g., 'Onion Granules for Oyster Sauce'). Use DESLY's branding colors if possible.",
                        "owner": "Marketing",
                        "due_by_day": 15,
                        "deliverable": "Branded 1-pager PDF",
                        "success_criteria": "PDF visually aligns with B2B professional standards and includes all key value points.",
                        "depends_on": [
                            "R5",
                            "O4"
                        ],
                        "status": "pending"
                    },
                    {
                        "task_id": "P2",
                        "task_name": "Draft Sample Proposal",
                        "description": "Create a formal proposal for a sample batch of 2-3 SKUs identified in R1 (e.g., 5kg each of Dehydrated Garlic Powder 98.8% purity and White Onion Flakes). Detail specs, pricing, and lead time for direct sourcing from Gujarat to China.",
                        "owner": "Sales Head",
                        "due_by_day": 16,
                        "deliverable": "Formal proposal document",
                        "success_criteria": "Proposal includes all commercial and technical terms for sample order.",
                        "depends_on": [
                            "R1",
                            "R5"
                        ],
                        "status": "pending"
                    },
                    {
                        "task_id": "P3",
                        "task_name": "Issue Free Sample Offer",
                        "description": "Based on call feedback, issue a formal offer for free samples (with DESLY covering nominal logistics) to expedite their R&D evaluation. Highlight compatibility with their need for consistent, high-purity ingredients.",
                        "owner": "Sales Executive",
                        "due_by_day": 17,
                        "deliverable": "Sample offer email with terms",
                        "success_criteria": "Offer is sent, making it easy for DESLY to accept and test products.",
                        "depends_on": [
                            "P2"
                        ],
                        "status": "pending"
                    }
                ]
            },
            {
                "phase_number": 4,
                "phase_name": "Negotiation & Onboarding",
                "duration_weeks": 2,
                "objective": "Convert sample approval into a pilot order and establish the supply agreement.",
                "tasks": [
                    {
                        "task_id": "N1",
                        "task_name": "Develop Tiered Pricing",
                        "description": "Prepare tiered pricing for bulk orders (e.g., 500kg, 1MT, 5MT+) of the pilot SKUs, factoring in direct export to China. Highlight cost savings vs. their current sourcing.",
                        "owner": "Sales Head",
                        "due_by_day": 21,
                        "deliverable": "Tiered price list",
                        "success_criteria": "Price list is competitive and offers clear volume discounts.",
                        "depends_on": [
                            "P2"
                        ],
                        "status": "pending"
                    },
                    {
                        "task_id": "N2",
                        "task_name": "Pilot SKU Contract Call",
                        "description": "Host a call to negotiate terms for the first commercial pilot order (e.g., 500kg of one SKU). Discuss logistics, payment terms, and quality assurance protocols aligned with Halal/Kosher standards.",
                        "owner": "Sales Head",
                        "due_by_day": 24,
                        "deliverable": "Verbal agreement on pilot order terms",
                        "success_criteria": "Key terms (volume, price, delivery) are agreed upon verbally.",
                        "depends_on": [
                            "P3",
                            "O2"
                        ],
                        "status": "pending"
                    },
                    {
                        "task_id": "N3",
                        "task_name": "Finalize Invoice & Agreement",
                        "description": "Issue a Proforma Invoice and draft a simple supply agreement for the pilot, incorporating quality specs (purity percentages), delivery terms, and dispute resolution.",
                        "owner": "Sales Admin",
                        "due_by_day": 26,
                        "deliverable": "Signed PI and supply agreement",
                        "success_criteria": "Documents are signed by both parties, triggering order.",
                        "depends_on": [
                            "N2"
                        ],
                        "status": "pending"
                    },
                    {
                        "task_id": "N4",
                        "task_name": "Coordinate Production & Dispatch",
                        "description": "Initiate production of the pilot order at the Bhanvad plant, ensuring compliance with agreed specs. Coordinate with logistics partner for reliable shipment to China with all necessary export documentation.",
                        "owner": "Logistics Manager",
                        "due_by_day": 28,
                        "deliverable": "Order dispatched with tracking details",
                        "success_criteria": "Pilot order is shipped on time with all documents provided to DESLY.",
                        "depends_on": [
                            "N3"
                        ],
                        "status": "pending"
                    }
                ]
            },
            {
                "phase_number": 5,
                "phase_name": "Scale & Strategic Expansion",
                "duration_weeks": 4,
                "objective": "Secure repeat business, expand SKU range, and explore strategic private label partnership.",
                "tasks": [
                    {
                        "task_id": "S1",
                        "task_name": "Collect Formal Feedback",
                        "description": "After DESLY receives and tests the pilot order, schedule a feedback call. Document their assessment of product quality, consistency, and suitability for their sauce formulations.",
                        "owner": "Quality Manager",
                        "due_by_day": 35,
                        "deliverable": "Structured feedback report",
                        "success_criteria": "Report captures specific, actionable feedback on product performance.",
                        "depends_on": [
                            "N4"
                        ],
                        "status": "pending"
                    },
                    {
                        "task_id": "S2",
                        "task_name": "Plan Cross-sell Strategy",
                        "description": "Using feedback and the original gap analysis (R1), propose adding 1-2 new Nexus SKUs to DESLY's regular order (e.g., dehydrated herbs for their sushi food line or specific spice blends).",
                        "owner": "BD Strategist",
                        "due_by_day": 42,
                        "deliverable": "Cross-sell proposal",
                        "success_criteria": "Proposal recommends specific new products with clear rationale.",
                        "depends_on": [
                            "S1",
                            "R1"
                        ],
                        "status": "pending"
                    },
                    {
                        "task_id": "S3",
                        "task_name": "Develop White-label Partnership Pitch",
                        "description": "Formalize the private label opportunity scan (R3) into a concrete proposal. Pitch a co-developed line of 'DESLY Premium Dry Mixes' (e.g., Dehydrated Vegetable Blend for Sauces) using Nexus's manufacturing and DESLY's brand/distribution.",
                        "owner": "BD Strategist",
                        "due_by_day": 49,
                        "deliverable": "White-label partnership deck",
                        "success_criteria": "Deck outlines a viable 3-product roadmap and commercial model.",
                        "depends_on": [
                            "R3",
                            "S1"
                        ],
                        "status": "pending"
                    },
                    {
                        "task_id": "S4",
                        "task_name": "Propose Exclusive Deal Framework",
                        "description": "For high-performing SKUs, propose an exclusive supply agreement for DESLY's region or product line, ensuring supply security and preferential pricing in return for volume commitments.",
                        "owner": "Sales Head",
                        "due_by_day": 56,
                        "deliverable": "Draft exclusivity agreement framework",
                        "success_criteria": "Framework outlines clear terms, benefits, and commitments for both parties.",
                        "depends_on": [
                            "S2",
                            "N4"
                        ],
                        "status": "pending"
                    }
                ]
            }
        ],
        "cross_phase_dependencies": [
            {
                "from_task": "R5",
                "to_task": "O1",
                "type": "sequential"
            },
            {
                "from_task": "O4",
                "to_task": "P1",
                "type": "sequential"
            },
            {
                "from_task": "P3",
                "to_task": "N2",
                "type": "sequential"
            }
        ],
        "meta": {
            "version": "2.0"
        }
    }
}


# PDF Viewer Widget
class company_task_widget(QWidget):
    def __init__(self, parent=None, commmon_widget=None, ):
        super().__init__(parent)
        self.commmon_widget = commmon_widget
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.company_common = company_common.company_common(commmon_widget=self.commmon_widget)
        self.phase_tab_widget = None  # Initialize as None
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)

        # Create container widgets for task display
        self.task_display_widget = None
        self.task_display_layout = None

        #self._update()  # Initial population of phase buttons

    def main_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        vertical_layout.addWidget(self.top_main_button())

        vertical_layout.addWidget(self._phase_button_list())

        # Create a container for phase content
        self.phase_content_widget = QWidget()
        self.phase_content_layout = QVBoxLayout(self.phase_content_widget)
        self.phase_content_layout.setContentsMargins(0, 0, 0, 0)
        vertical_layout.addWidget(self.phase_content_widget)

        return widget

    def top_main_button(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        top_button = self.sample_widget_template.pushButton(set_text='Client Company >>>>>> User company',
                                                            min_size=[0, 0],
                                                            max_size=[self.sample_widget_template.max_size, 58], )
        top_button.setFont(font)
        vertical_layout.addWidget(top_button)

        return widget

    def _phase_button_list(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        self.phase_horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget, set_spacing=5)

        return widget

    def update_phase_buttons(self, dic_data):
        """
        Clear existing phase buttons and create new ones based on the phase list

        :param phase_list: Dictionary containing phase information
        :return: None
        """
        # Extract phases from the nested dictionary structure
        phases = dic_data.get('engagement_plan', {}).get('phases', [])

        # Clear existing buttons from the horizontal layout
        self._clear_layout(self.phase_horizontal_layout)

        # Add new buttons for each phase
        for phase_data in phases:
            # Extract phase name - adjust this based on your actual data structure
            phase_name = phase_data.get('phase_name', 'Unknown Phase')

            # Create a button for this phase
            phase_button = self.sample_widget_template.pushButton(
                set_text=phase_name
            )

            # Optional: Store phase data with the button for later use
            phase_button.phase_data = phase_data
            phase_button.clicked.connect(lambda checked, data=phase_data: self.on_phase_button_clicked(data))

            # Add the button to the horizontal layout
            self.phase_horizontal_layout.addWidget(phase_button)

    def on_phase_button_clicked(self, phase_data):
        """
        Handle phase button click event

        :param phase_data: Dictionary containing data for the clicked phase
        :return: None
        """
        print(json.dumps(phase_data, indent=2))  # For debugging - print the phase data

        # Clear existing content in the phase content layout
        self._clear_layout(self.phase_content_layout)

        # Create a widget to hold all phase content
        phase_widget = QWidget()
        phase_layout = QVBoxLayout(phase_widget)
        phase_layout.setContentsMargins(0, 0, 0, 0)

        # Display the objective of the phase
        duration_weeks = str(phase_data.get('duration_weeks', '0'))
        duration_label = self.number_of_week_label(duration_weeks)
        phase_layout.addWidget(duration_label)

        # OBJECTIVE WIDGET
        objective = phase_data.get('objective', 'No objective provided')
        objective_widget = self.objective_widget(objective)
        phase_layout.addWidget(objective_widget)

        # TASK WIDGET - This will now be at the top
        task_list = phase_data.get('tasks', [])
        task_widget, task_display_widget = self.task_widget(task_list)
        phase_layout.addWidget(task_widget)

        # Store reference to task display widget
        self.task_display_widget = task_display_widget

        phase_layout.addStretch()

        # Add the phase widget to the phase content layout
        self.phase_content_layout.addWidget(phase_widget)

    def number_of_week_label(self, duration_weeks):
        '''
        Create a label to display the number of weeks for the phase duration
        :param duration_weeks: Duration in weeks to display
        :return: QLabel widget with formatted text
        '''
        label = self.sample_widget_template.label(set_text=f"Duration: {duration_weeks} weeks",
                                                  set_alighment=self.sample_widget_template.center_alignment)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        label.setFont(font)
        return label

    def objective_widget(self, objective):
        '''

        :return:
        '''

        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget, set_spacing=5)

        label = self.sample_widget_template.label(set_text=f"Objective: ",
                                                  set_alighment=self.sample_widget_template.center_alignment)

        horizontal_layout.addWidget(label)

        text_edit = QTextEdit()
        font = QFont()
        font.setPointSize(10)
        text_edit.setFont(font)
        text_edit.setReadOnly(True)
        text_edit.setText(objective)
        horizontal_layout.addWidget(text_edit)

        return widget

    def task_widget(self, task_list):
        '''

        :return:
        '''
        main_widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=main_widget)

        # Task buttons widget
        task_buttons_widget = self.sample_widget_template.widget_def()
        vertical_layout.addWidget(task_buttons_widget)
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=task_buttons_widget,
                                                                          set_spacing=5)
        a = 0
        for each in task_list:
            task_name = each.get('task_name', 'Unknown Task')
            task_button = self.sample_widget_template.pushButton(set_text=task_name)
            task_button.task_data = each
            task_button.clicked.connect(lambda checked, data=each: self.on_task_button_clicked(data))
            horizontal_layout.addWidget(task_button)
            a += 1

        # Create a dedicated widget for displaying task details
        self.task_display_container = QWidget()
        self.task_display_layout = QVBoxLayout(self.task_display_container)
        self.task_display_layout.setContentsMargins(10, 10, 10, 10)
        vertical_layout.addWidget(self.task_display_container)

        return main_widget, self.task_display_container

    def on_task_button_clicked(self, task_data):
        '''
        Handle task button click event

        :param task_data: Dictionary containing data for the clicked task
        :return: None
        '''
        print(f"Task clicked: {task_data.get('task_name', 'Unknown Task')}")
        print(json.dumps(task_data, indent=2))  # For debugging - print the task data

        # Clear existing content in the task display layout
        self._clear_layout(self.task_display_layout)

        # Create a widget to display task details
        task_details_widget = QWidget()
        task_details_layout = QVBoxLayout(task_details_widget)

        # Set a frame and style for better visibility
        #task_details_widget.setFrameStyle(QFrame.Box)
        #task_details_widget.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ccc; border-radius: 5px;")

        # Task Name
        task_name_label = QLabel(f"<h3>{task_data.get('task_name', 'Unknown Task')}</h3>")
        task_name_label.setAlignment(Qt.AlignCenter)
        task_details_layout.addWidget(task_name_label)

        # Add a separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        task_details_layout.addWidget(line)

        # Task ID
        task_id = task_data.get('task_id', 'N/A')
        task_id_label = QLabel(f"<b>Task ID:</b> {task_id}")
        task_details_layout.addWidget(task_id_label)

        # Description
        description = task_data.get('description', 'No description provided')
        desc_label = QLabel(f"<b>Description:</b>")
        task_details_layout.addWidget(desc_label)

        desc_text = QTextEdit()
        desc_text.setReadOnly(True)
        desc_text.setText(description)
        desc_text.setMaximumHeight(100)
        task_details_layout.addWidget(desc_text)

        # Owner
        owner = task_data.get('owner', 'Unknown Owner')
        owner_label = QLabel(f"<b>Owner:</b> {owner}")
        task_details_layout.addWidget(owner_label)

        # Due By Day
        due_by = task_data.get('due_by_day', 'N/A')
        due_label = QLabel(f"<b>Due By Day:</b> {due_by}")
        task_details_layout.addWidget(due_label)

        # Deliverable
        deliverable = task_data.get('deliverable', 'No deliverable specified')
        deliverable_label = QLabel(f"<b>Deliverable:</b> {deliverable}")
        deliverable_label.setWordWrap(True)
        task_details_layout.addWidget(deliverable_label)

        # Success Criteria
        success_criteria = task_data.get('success_criteria', 'No success criteria specified')
        success_label = QLabel(f"<b>Success Criteria:</b> {success_criteria}")
        success_label.setWordWrap(True)
        task_details_layout.addWidget(success_label)

        # Status
        status = task_data.get('status', 'unknown')
        status_label = QLabel(f"<b>Status:</b> {status}")

        # Color code the status
        if status == 'completed':
            status_label.setStyleSheet("color: green;")
        elif status == 'in_progress':
            status_label.setStyleSheet("color: blue;")
        elif status == 'blocked':
            status_label.setStyleSheet("color: red;")
        elif status == 'cancelled':
            status_label.setStyleSheet("color: gray;")
        else:
            status_label.setStyleSheet("color: orange;")

        task_details_layout.addWidget(status_label)

        # Dependencies
        depends_on = task_data.get('depends_on', [])
        if depends_on:
            depends_label = QLabel(f"<b>Depends On:</b> {', '.join(depends_on)}")
            task_details_layout.addWidget(depends_label)

        # Add stretch to push everything up
        task_details_layout.addStretch()

        # Add the task details widget to the task display layout
        self.task_display_layout.addWidget(task_details_widget)

    def _clear_layout(self, layout):
        """
        Helper method to recursively clear all widgets from a layout

        :param layout: QLayout to clear
        :return: None
        """
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self._clear_layout(item.layout())

    def _update(self, dic_data):
        '''

        :return:
        '''
        self.update_phase_buttons(dic_data)


