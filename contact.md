---
layout: default
title: Contact
permalink: /contact/
---
<section class="section">
  <div class="container section-header">
    <p class="eyebrow">Contact</p>
    <h2>Invite Louis or request materials</h2>
    <p class="section-desc">Send a note about interviews, speaking engagements, or course resources.</p>
  </div>
  <div class="container split">
    <form class="contact-form" action="mailto:lhyman@gmail.com" method="POST" enctype="text/plain">
      <label>
        Name
        <input type="text" name="name" required>
      </label>
      <label>
        Email
        <input type="email" name="email" required>
      </label>
      <label>
        Message
        <textarea name="message" rows="4" required></textarea>
      </label>
      <button type="submit" class="button primary full">Send email</button>
    </form>
    <div class="contact-details">
      <p>Prefer your own client? Email <a href="mailto:lhyman@gmail.com">lhyman@gmail.com</a> directly.</p>
      <p>For archival reference, all materials migrated from the former Wix site are preserved in the <a href="{{ '/old_files/' | relative_url }}">old_files</a> folder.</p>
    </div>
  </div>
</section>
